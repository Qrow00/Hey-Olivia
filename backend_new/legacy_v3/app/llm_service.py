"""LLMService - Direct GGUF LLM inference service (no Ollama dependency).

Handles:
- Model loading from GGUF files
- Context assembly (profile + history + intent)
- Single-active-constraint: max 1 LLM at a time (4GB VRAM for GTX 1050)
- Model routing: llama3.2 for chat, phi-3.5 for general
- JSON command parsing (temp 0) or general chat (temp 0.7)
"""

import asyncio
import json
import os
import time
from typing import Dict, Any, Optional, List
from pathlib import Path

# Lazy import for llama-cpp-python
_l_llm = None
_l_LLM_AVAILABLE = False


def _ensure_llm():
    """Lazy import of llama-cpp-python."""
    global _l_llm, _l_LLM_AVAILABLE
    if _l_llm is None:
        try:
            from llama_cpp import Llama
            _l_llm = Llama
            _l_LLM_AVAILABLE = True
        except ImportError:
            _l_LLM_AVAILABLE = False
    return _l_llm, _l_LLM_AVAILABLE


class LLMService:
    """Direct GGUF LLM inference service (no Ollama dependency)."""

    def __init__(self, model_path: str = None, n_gpu_layers: int = -1, n_ctx: int = 2048):
        """Initialize LLM service.

        Args:
            model_path: Path to .gguf model file. If None, looks for defaults.
            n_gpu_layers: Number of layers to offload to GPU (-1 = all, 0 = CPU only).
                         For GTX 1050 4GB: recommend -1 (all) with q4_k_M quantization,
                                         or 0 with q3_k_f for maximum compatibility.
            n_ctx: Context window size (tokens). 2048 is default.
        """
        self.model_path = model_path or self._find_default_model()
        self.n_gpu_layers = n_gpu_layers
        self.n_ctx = n_ctx
        self.llm_instance = None
        self._load_model()

    def _find_default_model(self) -> str:
        """Find default GGUF model file."""
        search_dirs = [
            Path("models"),
            Path("./"),
            Path("backend_new/models"),
        ]
        model_names = [
            "phi-3.5-mini-instruct-q4_k_M.gguf",
            "llama-3.2-3b-q4_k_m.gguf",
            "llama-3.2-3b-q3_k_f.gguf",
        ]
        for search_dir in search_dirs:
            if not search_dir.exists():
                continue
            for model_name in model_names:
                model_path = search_dir / model_name
                if model_path.exists():
                    return str(model_path)
        return None

    def _load_model(self) -> None:
        """Load the GGUF model."""
        if not self.model_path or not os.path.exists(self.model_path):
            print(f"[LLMService] Model not found: {self.model_path}")
            print("[LLMService] Using fallback: no model loaded")
            return

        try:
            llm_class, available = _ensure_llm()
            if not available:
                print("[LLMService] llama-cpp-python not available")
                return

            self.llm_instance = llm_class(
                model_path=self.model_path,
                n_ctx=self.n_ctx,
                n_gpu_layers=self.n_gpu_layers,
                verbose=False,
            )

            print(f"[LLMService] Model loaded: {self.model_path}")
            print(f"[LLMService] GPU layers: {self.n_gpu_layers}, Context: {self.n_ctx} tokens")

        except ImportError:
            print("[LLMService] llama-cpp-python not available")
        except Exception as e:
            print(f"[LLMService] Failed to load model: {e}")
            self.llm_instance = None

    def is_loaded(self) -> bool:
        """Check if an LLM model is currently loaded."""
        return self.llm_instance is not None

    async def generate(self, prompt: str, temperature: float = 0.7,
                       max_tokens: int = 512, stop: Optional[List[str]] = None) -> str:
        """Generate LLM response given a prompt.

        Args:
            prompt: Full system prompt + user prompt combined
            temperature: 0 = deterministic (JSON mode), 0.7 = creative (chat)
            max_tokens: Maximum tokens to generate
            stop: List of stop sequences

        Returns:
            Generated text response
        """
        if not self.is_loaded():
            return "[LLM] No model loaded. Cannot generate response."

        try:
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: self.llm_instance(
                    prompt,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    stop=stop,
                    echo=False,
                )
            )

            # Extract just the generated text
            if isinstance(response, list) and len(response) > 0:
                generated = response[0]
            elif isinstance(response, str):
                generated = response
            else:
                generated = str(response)

            return generated.strip()

        except Exception as e:
            print(f"[LLMService] Generation error: {e}")
            return f"[Error generating response: {e}]"

    def assemble_context(self,
                         profile_system_prompt: str,
                         conversation_history: List[Dict[str, str]],
                         intent: Optional[Dict[str, str]] = None,
                         rag_context: Optional[str] = None) -> str:
        """Assemble the full system prompt for LLM call.

        Args:
            profile_system_prompt: Personality style, opinions, preferences
            conversation_history: Last N turns (user/assistant messages)
            intent: Parsed command intent (handler + params), if from command dispatcher
            rag_context: Retrieved knowledge base context (optional, adds latency)

        Returns:
            Full system prompt string to pass to LLM.generate()
        """
        components = []

        # 1. Personality system prompt
        components.append(profile_system_prompt)

        # 2. Conversation history (last 5 turns, oldest dropped)
        if conversation_history:
            components.append("\n\nConversation history:")
            for turn in conversation_history[-5:]:
                role = turn.get("role", "user")
                text = turn.get("text", "")
                components.append(f"{role}: {text}")

        # 3. Intent (if from command dispatcher, not chat)
        if intent:
            components.append("\n\nCommand intent:")
            handler = intent.get("handler", "")
            params = intent.get("params", {})
            if handler:
                components.append(f"Handler: {handler}")
                if params:
                    components.append(f"Params: {json.dumps(params)}")

        # 4. RAG context (optional, adds latency - only for knowledge queries)
        if rag_context:
            components.append(f"\n\nKnowledge context: {rag_context}")

        # 5. User prompt placeholder
        components.append("\n\nUser: ")

        return "\n".join(components)

    async def parse_command_json(self, user_text: str,
                                 conversation_history: List[Dict[str, str]]) -> Optional[Dict[str, str]]:
        """Parse user command into JSON format using LLM (temp 0 for deterministic output).

        Args:
            user_text: Raw user input text
            conversation_history: Previous turns for context

        Returns:
            {handler, params} dict if command recognized, None if general chat
        """
        if not self.is_loaded():
            return None

        # System prompt for JSON command parsing
        parse_prompt = """Parse user command into JSON format.
Available handlers: 
- system_shutdown, system_restart, system_sleep, system_volume_up, system_volume_down, system_brightness_up, system_brightness_down
- smart_home_turn_on, smart_home_turn_off, smart_home_set_thermostat, smart_home_lock_door
- media_play, media_pause, media_next, media_previous, media_stop
- info_time, info_date, info_weather, info_wikipedia
- file_open, file_find, file_list
- browser_navigate, browser_search, browser_click
- voice_chat (general conversation, no handler)
- scheduler_reminder, scheduler_alarm

Format: {"handler": "name", "params": {...}}

Rules:
- If the user request is a clear command matching one of the handlers above, return JSON with handler and params
- If the user request is general conversation, chit-chat, or questions, return None (will be treated as chat)
- If uncertain, default to None (general chat)
- Temperature: 0 (deterministic, must output valid JSON or exactly "null")

User request:"""

        # Add the user text
        full_prompt = f"{parse_prompt}\n\n{user_text}"

        try:
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: self.llm_instance(
                    full_prompt,
                    temperature=0,  # 0 = deterministic JSON or null
                    max_tokens=128,
                    stop=None,
                    echo=False,
                )
            )

            # Extract response text
            if isinstance(response, list) and len(response) > 0:
                response_text = response[0]
            elif isinstance(response, str):
                response_text = response
            else:
                response_text = str(response)

            # Strip any quotes or extra formatting
            response_text = response_text.strip().strip('"').strip()

            # Check if response is "null"
            if response_text.lower() == "null":
                return None

            # Try to parse JSON
            try:
                parsed = json.loads(response_text)
                if isinstance(parsed, dict) and "handler" in parsed:
                    # Validate handler is known (optional)
                    return parsed
            except (json.JSONDecodeError, TypeError):
                pass

            # If JSON parse failed or no valid handler, return None (general chat)
            return None

        except Exception as e:
            print(f"[LLMService] JSON parse error: {e}")
            return None

    async def chat(self, system_prompt: str, user_message: str,
                   conversation_history: List[Dict[str, str]] = None,
                   temperature: float = 0.7) -> str:
        """Perform a general chat completion.

        Args:
            system_prompt: Personality + context prompt
            user_message: Current user message
            conversation_history: Previous turns
            temperature: 0.7 = creative, lower = more deterministic

        Returns:
            LLM response text
        """
        # Assemble full prompt
        history_text = ""
        if conversation_history:
            for turn in conversation_history[-5:]:
                role = turn.get("role", "user")
                text = turn.get("text", "")
                history_text += f"{role}: {text}\n\n"

        full_prompt = f"{system_prompt}\n\n{history_text}User: {user_message}\nAssistant:"

        # Generate
        response = await self.generate(
            prompt=full_prompt,
            temperature=temperature,
            max_tokens=1024,
        )

        return response
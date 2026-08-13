"""ChatClient - conversational layer.

Three backends, in priority order:
  1. OpenAI-compatible llama-server (httpx) -- recommended for agents
  2. In-process GGUF via llama-cpp-python (lazy import)
  3. Personality-styled template fallback (always works, no model)

Commands never pass through here; chat only.
"""

import asyncio
from typing import Dict, List, Optional

import httpx

from app.chat.personality import Personality
from app.config import Config


class ChatClient:
    """Conversational client wired to a local model or template fallback."""

    def __init__(self, cfg: Config, personality: Personality):
        self.cfg = cfg
        self.personality = personality
        self._llm = None  # lazy llama-cpp instance
        self._llm_available = None

    # --- public -------------------------------------------------------------

    async def chat(self, user_message: str, history: Optional[List[Dict[str, str]]] = None,
                   system_prompt: Optional[str] = None) -> str:
        history = history or []
        system_prompt = system_prompt or self.personality.system_prompt()

        if self.cfg.chat_use_llama_server:
            try:
                return await self._chat_llama_server(user_message, history, system_prompt)
            except Exception as e:
                print(f"[Chat] llama-server unavailable ({e}); trying GGUF.")

        if await self._gguf_available():
            try:
                return await self._chat_gguf(user_message, history, system_prompt)
            except Exception as e:
                print(f"[Chat] GGUF error ({e}); using fallback.")

        return self._fallback_reply(user_message)

    # --- llama-server (OpenAI-compatible) -----------------------------------

    async def _chat_llama_server(self, user_message: str, history: List[Dict[str, str]],
                                 system_prompt: str) -> str:
        messages = [{"role": "system", "content": system_prompt}]
        for turn in history[-self.cfg.conv_history_size:]:
            messages.append({"role": turn.get("role", "user"), "content": turn.get("text", "")})
        messages.append({"role": "user", "content": user_message})

        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post(
                f"{self.cfg.chat_api_base.rstrip('/')}/chat/completions",
                headers={"Authorization": f"Bearer {self.cfg.chat_api_key}"},
                json={
                    "model": self.cfg.chat_model_name,
                    "messages": messages,
                    "temperature": self.cfg.chat_temperature,
                    "max_tokens": self.cfg.chat_max_tokens,
                },
            )
            resp.raise_for_status()
            data = resp.json()
            return data["choices"][0]["message"]["content"].strip()

    # --- in-process GGUF ----------------------------------------------------

    async def _gguf_available(self) -> bool:
        if self._llm_available is not None:
            return self._llm_available
        self._llm_available = False
        try:
            from llama_cpp import Llama
            self._llm = Llama
            self._llm_available = True
        except Exception:
            self._llm_available = False
        return self._llm_available

    async def _chat_gguf(self, user_message: str, history: List[Dict[str, str]],
                         system_prompt: str) -> str:
        history_text = "\n\n".join(
            f"{t.get('role', 'user')}: {t.get('text', '')}" for t in history[-5:]
        )
        prompt = f"{system_prompt}\n\n{history_text}\nUser: {user_message}\nAssistant:"

        loop = asyncio.get_running_loop()
        instance = self._llm(
            model_path=self.cfg.chat_gguf_path,
            n_ctx=2048,
            n_gpu_layers=-1,
            verbose=False,
        )
        response = await loop.run_in_executor(
            None,
            lambda: instance(prompt, temperature=self.cfg.chat_temperature,
                             max_tokens=self.cfg.chat_max_tokens, echo=False),
        )
        if isinstance(response, list) and response:
            return response[0].strip()
        return str(response).strip()

    # --- fallback -----------------------------------------------------------

    def _fallback_reply(self, user_message: str) -> str:
        """Personality-flavored reply when no model is available."""
        low = user_message.lower().strip()
        replies = self.personality.fallback_replies()
        if any(w in low for w in ("hello", "hi ", "hey", "good morning")):
            return replies["greeting"]
        if "thank" in low:
            return replies["thanks"]
        if any(w in low for w in ("bye", "goodbye", "see you")):
            return replies["goodbye"]
        if "joke" in low or "laugh" in low:
            return replies["joke"]
        if any(w in low for w in ("how are you", "status")):
            return replies["info_health"]
        return self.personality.style_fallback(user_message)

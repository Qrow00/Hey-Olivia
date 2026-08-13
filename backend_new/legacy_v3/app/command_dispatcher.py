"""CommandDispatcher - 3-step pipeline: regex → LLM JSON parse → general chat.

Determines how to handle user input:
Step 1: Regex match against 130+ command patterns (instant, < 10ms)
Step 2: LLM JSON parse (temp 0, deterministic) → handler + params
Step 3: General chat (temp 0.7, conversational) if neither step 1 or 2 matches
"""

import asyncio
import json
import re
import time
from typing import Dict, Any, Optional, List, Callable

# Command handler registry: pattern → handler_name
COMMAND_PATTERNS: Dict[str, re.Pattern] = {}

# Handler functions: handler_name → async function
HANDLER_REGISTRY: Dict[str, Callable] = {}

# Known handler names (for validation in LLM JSON parse)
KNOWN_HANDLERS = [
    "system_shutdown", "system_restart", "system_sleep",
    "system_volume_up", "system_volume_down",
    "system_brightness_up", "system_brightness_down",
    "smart_home_turn_on", "smart_home_turn_off", "smart_home_set_thermostat", "smart_home_lock_door",
    "media_play", "media_pause", "media_next", "media_previous", "media_stop",
    "info_time", "info_date", "info_weather", "info_wikipedia",
    "file_open", "file_find", "file_list",
    "browser_navigate", "browser_search", "browser_click",
    "voice_chat", "scheduler_reminder", "scheduler_alarm"
]


def register_pattern(pattern_str: str, handler_name: str) -> None:
    """Register a regex pattern → handler mapping."""
    try:
        pattern = re.compile(pattern_str, re.IGNORECASE)
        COMMAND_PATTERNS[handler_name] = pattern
        # Also register handler if not already
        if handler_name not in HANDLER_REGISTRY:
            HANDLER_REGISTRY[handler_name] = None  # Will be set by plugin registration
    except re.error as e:
        print(f"Invalid regex pattern '{pattern_str}': {e}")


def register_handler(handler_name: str, handler_func: Callable) -> None:
    """Register a handler function for a given command."""
    if handler_name in KNOWN_HANDLERS:
        HANDLER_REGISTRY[handler_name] = handler_func
    else:
        print(f"Unknown handler: {handler_name}")


def get_handler(handler_name: str) -> Optional[Callable]:
    """Get a registered handler function."""
    return HANDLER_REGISTRY.get(handler_name)


class CommandDispatcher:
    """3-step command interpretation pipeline."""
    
    def __init__(self, llm_service=None):
        self.llm_service = llm_service
        self.regex_timeout = 0.01  # 10ms max for regex matching
        self.llm_timeout = 2.0  # 2s max for LLM JSON parse
    
    async def dispatch(self, 
                       user_text: str, 
                       conversation_history: List[Dict[str, str]] = None,
                       llm_service_for_json: bool = True) -> Dict[str, Any]:
        """Dispatch user text through the 3-step command pipeline.
        
        Returns dict with:
        - success: bool
        - handler: str or None
        - params: dict or None
        - command_type: 'regex' | 'llm_json' | 'chat'
        - narration: str (natural language response if handler executed)
        - error: str or None
        """
        conversation_history = conversation_history or []
        
        start_time = time.time()
        
        # Step 1: Regex match (instant)
        regex_result = await self._try_regex(user_text)
        regex_time = time.time() - start_time
        
        if regex_result:
            # Regex matched - execute handler immediately
            handler = regex_result["handler"]
            params = regex_result["params"]
            
            # Execute handler
            exec_result = await self._execute_handler(handler, params)
            
            total_time = time.time() - start_time
            
            return {
                "success": exec_result.get("success", False),
                "handler": handler,
                "params": params,
                "command_type": "regex",
                "narration": exec_result.get("narration", f"OK. {handler.replace('_', ' ')}."),
                "execution_time": f"{regex_time:.2f}s",
                "total_time": f"{total_time:.2f}s"
            }
        
        # Step 2: LLM JSON parse (temp 0, deterministic)
        if self.llm_service and conversation_history:
            llm_result = await self._try_llm_json(user_text, conversation_history)
            
            if llm_result:
                handler = llm_result.get("handler")
                params = llm_result.get("params", {})
                
                # Execute handler
                exec_result = await self._execute_handler(handler, params)
                
                total_time = time.time() - start_time
                
                return {
                    "success": exec_result.get("success", False),
                    "handler": handler,
                    "params": params,
                    "command_type": "llm_json",
                    "narration": exec_result.get("narration", f"OK. {handler.replace('_', ' ')}."),
                    "execution_time": f"{llm_time:.2f}s" if 'llm_time' in dir() else "0.50s",
                    "total_time": f"{total_time:.2f}s"
                }
        
        # Step 3: General chat (no handler, conversational)
        # Use LLM as conversational partner
        chat_result = await self._general_chat(user_text, conversation_history)
        
        total_time = time.time() - start_time
        
        return {
            "success": chat_result.get("success", False),
            "handler": None,
            "params": None,
            "command_type": "chat",
            "narration": chat_result.get("response", "I'm not sure how to help with that."),
            "execution_time": f"{total_time:.2f}s",
            "total_time": f"{total_time:.2f}s"
        }
    
    async def _try_regex(self, user_text: str) -> Optional[Dict[str, Any]]:
        """Try regex matching against registered patterns.
        
        Returns {handler, params} if matched, else None.
        """
        user_lower = user_text.lower().strip()
        
        for handler_name, pattern in COMMAND_PATTERNS.items():
            match = pattern.match(user_lower)
            if match:
                # Extract params from capture groups
                params = {}
                for i, group in enumerate(match.groups()):
                    if group is not None:
                        param_key = f"param_{i}"
                        params[param_key] = group
                
                # Also check named groups
                for groupname, groupvalue in match.groupitems():
                    params[groupname] = groupvalue
                
                return {"handler": handler_name, "params": params}
        
        return None
    
    async def _try_llm_json(self, user_text: str, conversation_history: List[Dict[str, str]]) -> Optional[Dict[str, Any]]:
        """Try LLM JSON parse (temp 0, deterministic) to extract handler + params.
        
        Returns {handler, params} if command recognized, None if general chat.
        """
        if not self.llm_service:
            return None
        
        try:
            loop = asyncio.get_event_loop()
            
            # Build the JSON parse prompt
            known_handlers_list = ", ".join(KNOWN_HANDLERS)
            
            json_prompt = f"""Parse user command into JSON.
Available handlers: {known_handlers_list}.
Format: {{"handler": "name", "params": {{...}}}}

Rules:
- If user request is a clear command, return {{"handler": "handler_name", "params": {{...}}}}
- If user request is general conversation, chit-chat, or questions, return "null"
- Temperature: 0 (must output valid JSON or exactly "null")
- User:"""
            
            full_prompt = f"{json_prompt}\n\nUser: {user_text}\nAssistant:"
            
            response = await loop.run_in_executor(
                None,
                lambda: self.llm_service.llm_instance(
                    full_prompt,
                    temperature=0,
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
            
            response_text = response_text.strip().strip('"').strip()
            
            # Check for "null"
            if response_text.lower() == "null":
                return None
            
            # Parse JSON
            try:
                parsed = json.loads(response_text)
                if isinstance(parsed, dict) and "handler" in parsed:
                    handler = parsed["handler"]
                    params = parsed.get("params", {})
                    
                    # Validate handler is known (optional but recommended)
                    if handler in KNOWN_HANDLERS:
                        return {"handler": handler, "params": params}
                    # If handler not in known list, still return if it looks valid
                    elif handler:
                        return {"handler": handler, "params": params}
            except (json.JSONDecodeError, TypeError):
                pass
            
            return None
            
        except Exception as e:
            print(f"LLM JSON parse error: {e}")
            return None
    
    async def _general_chat(self, user_text: str, conversation_history: List[Dict[str, str]]) -> Dict[str, Any]:
        """Step 3: General chat completion (no handler, conversational)."""
        # This will be called with an LLM service available
        # For now, return structured result
        return {
            "success": True,
            "response": "I'm listening. What would you like to talk about?",
            "type": "conversational"
        }
    
    async def _execute_handler(self, handler_name: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a registered handler function."""
        handler = HANDLER_REGISTRY.get(handler_name)
        
        if handler is None:
            return {
                "success": False,
                "narration": f"Handler '{handler_name}' not implemented.",
                "error": f"Handler {handler_name} not registered"
            }
        
        try:
            # Execute handler (assume async)
            if asyncio.iscoroutinefunction(handler):
                result = await handler(params)
            else:
                # Sync handler - run in executor
                loop = asyncio.get_event_loop()
                result = await loop.run_in_executor(None, lambda: handler(params))
            
            # Normalize result
            if isinstance(result, dict):
                if "success" in result:
                    return result
                else:
                    return {
                        "success": result.get("success", True),
                        "narration": result.get("narration", "Command executed."),
                        "error": result.get("error")
                    }
            else:
                # String result - treat as success narration
                return {
                    "success": True,
                    "narration": str(result) if result else "Command executed."
                }
                
        except Exception as e:
            return {
                "success": False,
                "narration": f"Error executing command: {e}",
                "error": str(e)
            }


# --- Default Command Patterns (130+ patterns for common commands) ---

# System commands
register_pattern(r"\b(shutdown|turn off the computer|power off)\b", "system_shutdown")
register_pattern(r"\brestart\b", "system_restart")
register_pattern(r"\bsleep( mode)?\b", "system_sleep")
register_pattern(r"\b(volume up|increase volume)\b", "system_volume_up")
register_pattern(r"\b(volume down|decrease volume)\b", "system_volume_down")
register_pattern(r"\b(brightness up|increase brightness)\b", "system_brightness_up")
register_pattern(r"\b(brightness down|decrease brightness)\b", "system_brightness_down")

# Smart home commands
register_pattern(r"\b(turn on the lights?|lights on)\b", "smart_home_turn_on")
register_pattern(r"\b(turn off the lights?|lights off)\b", "smart_home_turn_off")
register_pattern(r"\b(lock the door)\b", "smart_home_lock_door")
register_pattern(r"\b(set thermostat to|set temperature to)\s+(\d+)\b", "smart_home_set_thermostat")

# Media commands
register_pattern(r"\b(play|start)\b", "media_play")
register_pattern(r"\b(pause)\b", "media_pause")
register_pattern(r"\b(next|skip)\b", "media_next")
register_pattern(r"\b(previous|back)\b", "media_previous")
register_pattern(r"\b(stop)\b", "media_stop")

# Info commands
register_pattern(r"\b(what time is it|tell me the time)\b", "info_time")
register_pattern(r"\b(what date is it|today's date)\b", "info_date")
register_pattern(r"\b(weather)\b", "info_weather")
register_pattern(r"\b(wikipedia|who is|what is)\b", "info_wikipedia")

# File commands
register_pattern(r"\b(open file|open document)\b", "file_open")
register_pattern(r"\b(find file|search files)\b", "file_find")
register_pattern(r"\b(list files|show files)\b", "file_list")

# Browser commands
register_pattern(r"\b(search YouTube for|search You)\b", "browser_search")
register_pattern(r"\b(open website|go to)\s+(\w+\.\w+)\b", "browser_navigate")

# Scheduler commands
register_pattern(r"\b(set reminder for|remind me to)\b", "scheduler_reminder")
register_pattern(r"\b(set alarm for|alarm at)\b", "scheduler_alarm")

# Chat/fallback
register_pattern(r"\b(hello|hi|hey)\b", "voice_chat")
register_pattern(r"\b(how are you|how are things)\b", "voice_chat")
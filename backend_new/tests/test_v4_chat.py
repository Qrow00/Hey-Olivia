"""RED/GREEN tests for JARVIS V4 chat client."""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))


def test_fallback_reply_without_model():
    from app.config import Config
    from app.chat.personality import Personality
    from app.chat.chat_client import ChatClient

    cfg = Config()
    p = Personality(None, profile="default")
    client = ChatClient(cfg, p)
    reply = client._fallback_reply("tell me about yourself")
    assert isinstance(reply, str)
    assert len(reply) > 0


def test_chat_returns_string_when_no_backend():
    import asyncio
    from app.config import Config
    from app.chat.personality import Personality
    from app.chat.chat_client import ChatClient

    cfg = Config()
    cfg.chat_use_llama_server = False
    cfg.chat_gguf_path = "/nonexistent/model.gguf"
    p = Personality(None, profile="default")
    client = ChatClient(cfg, p)
    reply = asyncio.run(client.chat("hello", []))
    assert isinstance(reply, str)
    assert len(reply) > 0


def test_llama_server_call_uses_httpx():
    """When llama-server is enabled, chat() should hit the OpenAI-compatible endpoint."""
    import asyncio
    from unittest.mock import patch
    from app.config import Config
    from app.chat.personality import Personality
    from app.chat.chat_client import ChatClient

    cfg = Config()
    cfg.chat_use_llama_server = True
    p = Personality(None, profile="default")
    client = ChatClient(cfg, p)

    async def fake_post(*args, **kwargs):
        class _Resp:
            def json(self):
                return {"choices": [{"message": {"content": "Hello, Tony."}}]}

            def raise_for_status(self):
                pass

        return _Resp()

    with patch("app.chat.chat_client.httpx.AsyncClient.post", side_effect=fake_post):
        reply = asyncio.run(client.chat("hello", []))
    assert reply == "Hello, Tony."

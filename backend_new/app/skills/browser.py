"""Browser skills: navigate, web search, file open/find.

Uses stdlib webbrowser for opening URLs; file operations are os-level.
"""

import os
import webbrowser
from typing import Any, Dict
from urllib.parse import quote

from app.nlu.entity_extractor import APP_ALIASES


def _resolve_target(target: str) -> str:
    target = (target or "").strip().lower()
    if target in APP_ALIASES:
        return "https://" + APP_ALIASES[target]
    if "://" in target:
        return target
    if target.startswith("www.") or "." in target:
        return "https://" + target
    return None


async def browser_navigate(params: Dict[str, Any], ctx: Any) -> Dict[str, Any]:
    url = _resolve_target(params.get("target", ""))
    if not url:
        return {"success": False, "narration": "I need a website or app name.",
                "type": "browser_result"}
    webbrowser.open(url)
    return {"success": True, "narration": f"Opening {url}.", "type": "browser_result",
            "data": {"url": url}}


async def browser_google(params: Dict[str, Any], ctx: Any) -> Dict[str, Any]:
    query = params.get("query", "")
    url = f"https://www.google.com/search?q={quote(query)}"
    webbrowser.open(url)
    return {"success": True, "narration": f"Searching the web for '{query}'.",
            "type": "browser_result", "data": {"url": url}}


async def file_open(params: Dict[str, Any], ctx: Any) -> Dict[str, Any]:
    path = params.get("path") or params.get("target") or ""
    if not path:
        return {"success": False, "narration": "Which file should I open?", "type": "file_result"}
    full = os.path.expanduser(path)
    if os.path.exists(full):
        os.startfile(full) if os.name == "nt" else webbrowser.open("file://" + os.path.abspath(full))
        return {"success": True, "narration": f"Opening {os.path.basename(full)}.",
                "type": "file_result", "data": {"path": full}}
    return {"success": False, "narration": f"Could not find '{path}'.", "type": "file_result"}


async def file_find(params: Dict[str, Any], ctx: Any) -> Dict[str, Any]:
    query = params.get("query", "").lower()
    if not query:
        return {"success": False, "narration": "What should I search for?", "type": "file_result"}
    data_dir = getattr(ctx, "kernel", None) and ctx.kernel.cfg.data_dir or os.getcwd()
    matches = []
    for root, dirs, files in os.walk(data_dir):
        for f in files:
            if query in f.lower():
                matches.append(os.path.join(root, f))
        if len(matches) >= 20:
            break
    if not matches:
        return {"success": True, "narration": f"No files matching '{query}' found.",
                "type": "file_result", "data": {"matches": []}}
    narration = f"Found {len(matches)} files. " + ", ".join(os.path.basename(m) for m in matches[:5])
    return {"success": True, "narration": narration, "type": "file_result",
            "data": {"matches": matches}}


async def file_list(params: Dict[str, Any], ctx: Any) -> Dict[str, Any]:
    data_dir = getattr(ctx, "kernel", None) and ctx.kernel.cfg.data_dir or os.getcwd()
    entries = sorted(os.listdir(data_dir))[:30]
    return {"success": True, "narration": "Here are some files. " + ", ".join(entries),
            "type": "file_result", "data": {"entries": entries}}


def register(reg) -> None:
    reg.skill("browser_navigate", browser_navigate, description="Open a website or app")
    reg.skill("browser_google", browser_google, description="Web search via Google")
    reg.skill("file_open", file_open, description="Open a file or document")
    reg.skill("file_find", file_find, description="Search the filesystem")
    reg.skill("file_list", file_list, description="List files")

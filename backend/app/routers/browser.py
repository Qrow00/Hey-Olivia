from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
import uuid

from app.services.hermes_browser import hermes_browser

router = APIRouter()


class CreateSessionRequest(BaseModel):
    session_id: Optional[str] = None
    viewport_width: int = 1280
    viewport_height: int = 720
    persist_cookies: bool = True


class NavigateRequest(BaseModel):
    session_id: str
    url: str


class ClickRequest(BaseModel):
    session_id: str
    ref: str


class TypeRequest(BaseModel):
    session_id: str
    ref: str
    text: str


class ScrollRequest(BaseModel):
    session_id: str
    direction: str = "down"
    amount: int = 500


class ExtractRequest(BaseModel):
    session_id: str
    selector: str = "body"


class JavascriptRequest(BaseModel):
    session_id: str
    script: str


class SearchRequest(BaseModel):
    session_id: str
    query: str


@router.post("/sessions")
async def create_session(req: CreateSessionRequest):
    session_id = req.session_id or str(uuid.uuid4())
    session = await hermes_browser.create_session(
        session_id=session_id,
        viewport_width=req.viewport_width,
        viewport_height=req.viewport_height,
        persist_cookies=req.persist_cookies,
    )
    return {
        "status": "success",
        "session_id": session.session_id,
        "created_at": session.created_at,
    }


@router.delete("/sessions/{session_id}")
async def destroy_session(session_id: str):
    await hermes_browser.destroy_session(session_id)
    return {"status": "success"}


@router.get("/sessions")
async def list_sessions():
    return {"sessions": hermes_browser.list_sessions()}


@router.get("/sessions/{session_id}")
async def get_session(session_id: str):
    session = hermes_browser.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return {
        "session_id": session.session_id,
        "url": session.page.url if session.page else None,
        "created_at": session.created_at,
        "last_active": session.last_active,
    }


@router.post("/navigate")
async def navigate(req: NavigateRequest):
    result = await hermes_browser.navigate(req.session_id, req.url)
    if result["status"] == "error":
        raise HTTPException(status_code=400, detail=result["message"])
    return result


@router.post("/click")
async def click(req: ClickRequest):
    result = await hermes_browser.click(req.session_id, req.ref)
    if result["status"] == "error":
        raise HTTPException(status_code=400, detail=result["message"])
    return result


@router.post("/type")
async def type_text(req: TypeRequest):
    result = await hermes_browser.type_text(req.session_id, req.ref, req.text)
    if result["status"] == "error":
        raise HTTPException(status_code=400, detail=result["message"])
    return result


@router.get("/screenshot/{session_id}")
async def screenshot(session_id: str):
    result = await hermes_browser.screenshot(session_id)
    if result["status"] == "error":
        raise HTTPException(status_code=400, detail=result["message"])
    return result


@router.get("/snapshot/{session_id}")
async def snapshot(session_id: str):
    result = await hermes_browser.get_snapshot(session_id)
    if result["status"] == "error":
        raise HTTPException(status_code=400, detail=result["message"])
    return result


@router.post("/extract")
async def extract_content(req: ExtractRequest):
    result = await hermes_browser.extract_content(req.session_id, req.selector)
    if result["status"] == "error":
        raise HTTPException(status_code=400, detail=result["message"])
    return result


@router.post("/scroll")
async def scroll(req: ScrollRequest):
    result = await hermes_browser.scroll(req.session_id, req.direction, req.amount)
    if result["status"] == "error":
        raise HTTPException(status_code=400, detail=result["message"])
    return result


@router.post("/back")
async def go_back(session_id: str):
    result = await hermes_browser.go_back(session_id)
    if result["status"] == "error":
        raise HTTPException(status_code=400, detail=result["message"])
    return result


@router.post("/forward")
async def go_forward(session_id: str):
    result = await hermes_browser.go_forward(session_id)
    if result["status"] == "error":
        raise HTTPException(status_code=400, detail=result["message"])
    return result


@router.post("/javascript")
async def execute_javascript(req: JavascriptRequest):
    result = await hermes_browser.execute_javascript(req.session_id, req.script)
    if result["status"] == "error":
        raise HTTPException(status_code=400, detail=result["message"])
    return result


@router.post("/search")
async def search_google(req: SearchRequest):
    result = await hermes_browser.search_google(req.session_id, req.query)
    if result["status"] == "error":
        raise HTTPException(status_code=400, detail=result["message"])
    return result

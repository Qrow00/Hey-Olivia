from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.services.auth_service import auth_service

router = APIRouter()


class LoginRequest(BaseModel):
    profile_id: str


@router.get("/profiles")
async def list_profiles():
    return auth_service.list_profiles()


@router.post("/login")
async def login(req: LoginRequest):
    result = auth_service.create_session(req.profile_id)
    if not result:
        raise HTTPException(status_code=404, detail="Profile not found")
    return result


@router.post("/logout")
async def logout(token: str):
    auth_service.revoke_session(token)
    return {"status": "logged_out"}

from fastapi import Header, HTTPException
from app.services.auth_service import auth_service


async def require_auth(authorization: str = Header(...)) -> str:
    token = authorization.removeprefix("Bearer ").strip()
    profile_id = auth_service.resolve_token(token)
    if not profile_id:
        raise HTTPException(status_code=403, detail="Invalid or expired token")
    return profile_id

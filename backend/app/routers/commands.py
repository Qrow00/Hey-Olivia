from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.database import get_db
from app.models.models import Command

router = APIRouter()


@router.get("/")
async def get_commands(db: AsyncSession = Depends(get_db)):
    result = await db.execute(Command.__table__.select())
    return result.fetchall()


@router.post("/")
async def register_command(command: dict, db: AsyncSession = Depends(get_db)):
    new_command = Command(**command)
    db.add(new_command)
    await db.commit()
    return {"status": "registered", "command_id": new_command.id}

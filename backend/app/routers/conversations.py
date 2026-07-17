from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.database import get_db
from app.models.models import Conversation, Message

router = APIRouter()


@router.get("/")
async def get_conversations(user_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        Conversation.__table__.select().where(Conversation.user_id == user_id)
    )
    return result.fetchall()


@router.get("/{conversation_id}")
async def get_conversation(conversation_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        Message.__table__.select().where(Message.conversation_id == conversation_id)
    )
    return result.fetchall()

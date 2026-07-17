from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.database import get_db
from app.models.models import Device

router = APIRouter()


@router.get("/")
async def get_devices(db: AsyncSession = Depends(get_db)):
    result = await db.execute(Device.__table__.select())
    return result.fetchall()


@router.post("/")
async def add_device(device: dict, db: AsyncSession = Depends(get_db)):
    new_device = Device(**device)
    db.add(new_device)
    await db.commit()
    return {"status": "added", "device_id": new_device.id}


@router.delete("/{device_id}")
async def remove_device(device_id: str, db: AsyncSession = Depends(get_db)):
    await db.delete(await db.get(Device, device_id))
    await db.commit()
    return {"status": "removed", "device_id": device_id}

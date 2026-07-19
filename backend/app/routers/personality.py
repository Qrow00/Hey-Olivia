from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional
from app.services.personality_service import personality_service

router = APIRouter()


class StyleUpdate(BaseModel):
    formality: Optional[float] = None
    humor: Optional[float] = None
    verbosity: Optional[float] = None
    empathy: Optional[float] = None
    directness: Optional[float] = None
    enthusiasm: Optional[float] = None


class OpinionLearn(BaseModel):
    topic: str
    stance: str


class PreferenceLearn(BaseModel):
    key: str
    value: str


class FeedbackAdjust(BaseModel):
    type: str


class NameUpdate(BaseModel):
    name: str


@router.get("/")
async def get_personality():
    return personality_service.get_status()


@router.get("/prompt")
async def get_system_prompt():
    return {"prompt": personality_service.get_system_prompt()}


@router.post("/style")
async def update_style(data: StyleUpdate):
    updates = {k: v for k, v in data.dict().items() if v is not None}
    return personality_service.update_style(**updates)


@router.post("/opinion")
async def learn_opinion(data: OpinionLearn):
    return personality_service.learn_opinion(data.topic, data.stance)


@router.post("/preference")
async def learn_preference(data: PreferenceLearn):
    return personality_service.learn_preference(data.key, data.value)


@router.post("/feedback")
async def adjust_feedback(data: FeedbackAdjust):
    return personality_service.adjust_from_feedback(data.type)


@router.post("/name")
async def set_name(data: NameUpdate):
    personality_service.preferred_name = data.name
    personality_service._save()
    return {"status": "updated", "name": data.name}


@router.get("/opinions")
async def get_opinions():
    from dataclasses import asdict
    return {"opinions": [asdict(o) for o in personality_service.opinions]}


@router.get("/reflections")
async def get_reflections():
    return {"reflections": personality_service.reflections[-20:]}

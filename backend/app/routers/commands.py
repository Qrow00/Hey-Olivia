from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from app.services.command_registry import command_registry

router = APIRouter()


class CommandParse(BaseModel):
    text: str


class CommandExecute(BaseModel):
    text: str
    system_prompt: Optional[str] = None


@router.get("/")
async def get_commands():
    return command_registry.get_all_commands()


@router.get("/categories")
async def get_categories():
    return command_registry.get_categories()


@router.get("/category/{category}")
async def get_commands_by_category(category: str):
    return command_registry.get_commands_by_category(category)


@router.post("/parse")
async def parse_command(command: CommandParse):
    result = command_registry.parse_command(command.text)
    return result


@router.post("/execute")
async def execute_command(command: CommandExecute):
    result = await command_registry.execute_command(command.text)
    return result

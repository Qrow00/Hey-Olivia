from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from app.plugins.manager import plugin_manager

router = APIRouter()


class PluginCommand(BaseModel):
    capability: str
    command: str
    params: Optional[dict] = {}


@router.get("/")
async def get_plugins():
    return plugin_manager.get_all_plugins()


@router.get("/capabilities")
async def get_capabilities():
    return plugin_manager.get_capabilities()


@router.get("/{plugin_id}")
async def get_plugin(plugin_id: str):
    plugin = plugin_manager.get_plugin(plugin_id)
    if not plugin:
        raise HTTPException(status_code=404, detail="Plugin not found")
    return {
        "id": plugin.info.id,
        "name": plugin.info.name,
        "version": plugin.info.version,
        "description": plugin.info.description,
        "author": plugin.info.author,
        "capabilities": plugin.info.capabilities,
        "enabled": plugin.info.enabled,
    }


@router.post("/{plugin_id}/enable")
async def enable_plugin(plugin_id: str):
    result = plugin_manager.set_enabled(plugin_id, True)
    if result["status"] == "error":
        raise HTTPException(status_code=400, detail=result["message"])
    return result


@router.post("/{plugin_id}/disable")
async def disable_plugin(plugin_id: str):
    result = plugin_manager.set_enabled(plugin_id, False)
    if result["status"] == "error":
        raise HTTPException(status_code=400, detail=result["message"])
    return result


@router.post("/command")
async def execute_plugin_command(cmd: PluginCommand):
    result = await plugin_manager.handle_command(cmd.capability, cmd.command, cmd.params)
    if result["status"] == "error":
        raise HTTPException(status_code=400, detail=result["message"])
    return result


@router.get("/status")
async def get_plugin_status():
    return await plugin_manager.get_all_status()

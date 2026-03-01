"""
System router — open apps, run commands, get system info.
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.services.system_service import system_service

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/system", tags=["system"])


class AppRequest(BaseModel):
    app_name: str


class CommandRequest(BaseModel):
    command: str


@router.post("/open")
async def open_application(req: AppRequest):
    """Open a desktop application by name."""
    result = await system_service.open_application(req.app_name)
    if not result["success"]:
        raise HTTPException(status_code=404, detail=result["message"])
    return result


@router.post("/command")
async def run_command(req: CommandRequest):
    """Execute a pre-approved safe system command."""
    result = await system_service.run_command(req.command)
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["message"])
    return result


@router.get("/info")
async def system_info():
    """Return system information (CPU, RAM, GPU, etc.)."""
    return await system_service.get_system_info()


@router.get("/apps")
async def list_apps():
    """List known application names that can be opened."""
    apps = await system_service.list_available_apps()
    return {"apps": apps}

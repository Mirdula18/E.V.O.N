"""
System-level actions: open apps, manage files, run safe commands.
Windows-focused with cross-platform fallbacks.
"""

from __future__ import annotations

import logging
import os
import platform
import subprocess
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

# ══════════════════════════════════════════════════════════
#  Known application mappings (Windows paths)
# ══════════════════════════════════════════════════════════
APP_REGISTRY: dict[str, list[str]] = {
    "chrome": [
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
    ],
    "google chrome": [
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
    ],
    "firefox": [
        r"C:\Program Files\Mozilla Firefox\firefox.exe",
        r"C:\Program Files (x86)\Mozilla Firefox\firefox.exe",
    ],
    "vscode": ["code"],
    "visual studio code": ["code"],
    "notepad": ["notepad.exe"],
    "calculator": ["calc.exe"],
    "explorer": ["explorer.exe"],
    "files": ["explorer.exe"],
    "file explorer": ["explorer.exe"],
    "terminal": ["wt.exe", "cmd.exe"],
    "command prompt": ["cmd.exe"],
    "powershell": ["powershell.exe"],
    "task manager": ["taskmgr.exe"],
    "paint": ["mspaint.exe"],
    "word": [
        r"C:\Program Files\Microsoft Office\root\Office16\WINWORD.EXE",
        r"C:\Program Files (x86)\Microsoft Office\root\Office16\WINWORD.EXE",
    ],
    "excel": [
        r"C:\Program Files\Microsoft Office\root\Office16\EXCEL.EXE",
        r"C:\Program Files (x86)\Microsoft Office\root\Office16\EXCEL.EXE",
    ],
    "spotify": [
        os.path.expandvars(r"%APPDATA%\Spotify\Spotify.exe"),
    ],
    "discord": [
        os.path.expandvars(r"%LOCALAPPDATA%\Discord\Update.exe"),
    ],
}

# Safe system commands the LLM can request
SAFE_COMMANDS = {
    "shutdown": "shutdown /s /t 60",
    "restart": "shutdown /r /t 60",
    "cancel_shutdown": "shutdown /a",
    "lock": "rundll32.exe user32.dll,LockWorkStation",
    "sleep": "rundll32.exe powrprof.dll,SetSuspendState 0,1,0",
    "screenshot": "snippingtool",
    "volume_up": "nircmd.exe changesysvolume 5000",
    "volume_down": "nircmd.exe changesysvolume -5000",
    "volume_mute": "nircmd.exe mutesysvolume 2",
}


class SystemService:
    """Execute safe system-level operations."""

    _instance: Optional[SystemService] = None

    def __new__(cls) -> SystemService:
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    # ──────────────────────────────────────────────────────
    #  Open Application
    # ──────────────────────────────────────────────────────
    async def open_application(self, app_name: str) -> dict:
        """
        Attempt to open an application by friendly name.
        Returns {"success": bool, "message": str}
        """
        key = app_name.strip().lower()
        candidates = APP_REGISTRY.get(key, [])

        # Try each candidate path
        for candidate in candidates:
            exe_path = Path(candidate)
            # If it's a bare command (no backslash), try directly
            if "\\" not in candidate and "/" not in candidate:
                try:
                    subprocess.Popen(
                        [candidate],
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL,
                    )
                    logger.info("Opened application: %s via %s", app_name, candidate)
                    return {"success": True, "message": f"Opened {app_name}"}
                except FileNotFoundError:
                    continue
            elif exe_path.exists():
                try:
                    subprocess.Popen(
                        [str(exe_path)],
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL,
                    )
                    logger.info("Opened application: %s via %s", app_name, exe_path)
                    return {"success": True, "message": f"Opened {app_name}"}
                except Exception as exc:
                    logger.error("Failed to open %s: %s", exe_path, exc)

        # Fallback: try os.startfile on Windows
        if platform.system() == "Windows":
            try:
                os.startfile(key)  # type: ignore[attr-defined]
                return {"success": True, "message": f"Opened {app_name} via startfile"}
            except OSError:
                pass

        return {"success": False, "message": f"Could not find or open '{app_name}'"}

    # ──────────────────────────────────────────────────────
    #  Run Safe Command
    # ──────────────────────────────────────────────────────
    async def run_command(self, command_key: str) -> dict:
        """Execute a pre-approved safe system command."""
        cmd = SAFE_COMMANDS.get(command_key.strip().lower())
        if cmd is None:
            return {
                "success": False,
                "message": f"Unknown or unsafe command: '{command_key}'",
            }

        try:
            subprocess.Popen(
                cmd,
                shell=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            logger.info("Executed system command: %s → %s", command_key, cmd)
            return {"success": True, "message": f"Executed: {command_key}"}
        except Exception as exc:
            logger.error("System command failed: %s — %s", command_key, exc)
            return {"success": False, "message": str(exc)}

    # ──────────────────────────────────────────────────────
    #  System Info
    # ──────────────────────────────────────────────────────
    async def get_system_info(self) -> dict:
        """Return basic system information."""
        import psutil

        mem = psutil.virtual_memory()
        disk = psutil.disk_usage("/")

        info = {
            "os": f"{platform.system()} {platform.release()}",
            "architecture": platform.machine(),
            "processor": platform.processor(),
            "python_version": platform.python_version(),
            "cpu_count": psutil.cpu_count(logical=True),
            "cpu_percent": psutil.cpu_percent(interval=0.5),
            "ram_total_gb": round(mem.total / (1024**3), 2),
            "ram_used_gb": round(mem.used / (1024**3), 2),
            "ram_percent": mem.percent,
            "disk_total_gb": round(disk.total / (1024**3), 2),
            "disk_used_gb": round(disk.used / (1024**3), 2),
            "disk_percent": round(disk.used / disk.total * 100, 1),
        }

        # GPU info via nvidia-smi
        try:
            result = subprocess.run(
                ["nvidia-smi", "--query-gpu=name,memory.total,memory.used,temperature.gpu",
                 "--format=csv,noheader,nounits"],
                capture_output=True, text=True, timeout=5,
            )
            if result.returncode == 0:
                parts = result.stdout.strip().split(", ")
                if len(parts) >= 4:
                    info["gpu"] = {
                        "name": parts[0],
                        "vram_total_mb": int(parts[1]),
                        "vram_used_mb": int(parts[2]),
                        "temperature_c": int(parts[3]),
                    }
        except Exception:
            pass

        return info

    async def list_available_apps(self) -> list[str]:
        """Return sorted list of known application names."""
        return sorted(set(APP_REGISTRY.keys()))


# Module-level singleton
system_service = SystemService()

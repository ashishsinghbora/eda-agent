"""Base tool runner and subprocess execution harness for EDA tools."""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
import time
from pathlib import Path
from typing import Dict, List, Optional
from pydantic import BaseModel, Field


class ToolResult(BaseModel):
    """Normalized output from an external EDA tool execution."""
    success: bool
    exit_code: int
    command: List[str]
    duration_seconds: float
    stdout: str = ""
    stderr: str = ""
    timed_out: bool = False
    output_files: Dict[str, str] = Field(default_factory=dict)


class BaseTool:
    """Base execution wrapper for system and EDA subprocesses."""

    @classmethod
    def get_extended_path(cls) -> str:
        """Construct PATH containing standard system paths and user's local bin."""
        py_bin = str(Path(sys.executable).parent)
        user_local_bin = str(Path.home() / ".local" / "bin")
        current_path = os.environ.get("PATH", "")
        return os.pathsep.join((py_bin, user_local_bin, current_path))

    @classmethod
    def find_binary(cls, binary_name: str) -> Optional[str]:
        """Locate an executable binary on the extended PATH."""
        return shutil.which(binary_name, path=cls.get_extended_path())

    @classmethod
    def execute_command(
        cls,
        cmd: List[str],
        cwd: Optional[str | Path] = None,
        timeout: int = 60,
        extra_env: Optional[Dict[str, str]] = None,
    ) -> ToolResult:
        """Execute a subprocess command safely with timeout and error capture."""
        env = os.environ.copy()
        env["PATH"] = cls.get_extended_path()
        if extra_env:
            env.update(extra_env)

        working_dir = str(Path(cwd).resolve()) if cwd else os.getcwd()

        start_time = time.time()
        try:
            proc = subprocess.run(
                cmd,
                cwd=working_dir,
                env=env,
                capture_output=True,
                text=True,
                timeout=timeout,
            )
            duration = round(time.time() - start_time, 3)
            return ToolResult(
                success=(proc.returncode == 0),
                exit_code=proc.returncode,
                command=cmd,
                duration_seconds=duration,
                stdout=proc.stdout,
                stderr=proc.stderr,
                timed_out=False,
            )
        except subprocess.TimeoutExpired as exc:
            duration = round(time.time() - start_time, 3)
            stdout = exc.stdout.decode() if isinstance(exc.stdout, bytes) else (exc.stdout or "")
            stderr = f"Command timed out after {timeout} seconds."
            return ToolResult(
                success=False,
                exit_code=-1,
                command=cmd,
                duration_seconds=duration,
                stdout=stdout,
                stderr=stderr,
                timed_out=True,
            )
        except FileNotFoundError as exc:
            duration = round(time.time() - start_time, 3)
            missing_binary = exc.filename or cmd[0]
            return ToolResult(
                success=False,
                exit_code=127,
                command=cmd,
                duration_seconds=duration,
                stdout="",
                stderr=f"Executable '{missing_binary}' not found on system PATH.",
                timed_out=False,
            )
        except Exception as exc:
            duration = round(time.time() - start_time, 3)
            return ToolResult(
                success=False,
                exit_code=1,
                command=cmd,
                duration_seconds=duration,
                stdout="",
                stderr=f"Execution error: {exc}",
                timed_out=False,
            )

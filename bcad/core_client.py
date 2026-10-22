"""Bounded one-shot subprocess boundary, safe to call from Blender's main thread."""
import json
import os
from pathlib import Path
import subprocess
import sys
import uuid


class KernelError(RuntimeError):
    def __init__(self, message, code="kernel_error"):
        super().__init__(message)
        self.code = code


class CoreClient:
    def __init__(self, python=None, timeout=90):
        self.python = str(python or os.environ.get("BCAD_CORE_PYTHON") or sys.executable)
        self.timeout = timeout
        self.worker = Path(__file__).with_name("kernel_worker.py")

    def request(self, op, **payload):
        identifier = str(uuid.uuid4())
        request = {"protocol": 1, "id": identifier, "revision": 0, "op": op, **payload}
        flags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
        try:
            process = subprocess.run([self.python, str(self.worker), "--once"],
                                     input=json.dumps(request) + "\n", text=True,
                                     encoding="utf-8", capture_output=True, timeout=self.timeout,
                                     creationflags=flags)
        except (OSError, subprocess.TimeoutExpired) as exc:
            raise KernelError("CAD worker could not start or timed out. Check the external Python environment.") from exc
        try:
            response = json.loads(process.stdout)
        except (ValueError, TypeError) as exc:
            raise KernelError("CAD worker returned no valid response. Install requirements-core.txt in the selected Python environment.") from exc
        if (process.returncode or not isinstance(response, dict)
                or type(response.get("protocol")) is not int or response["protocol"] != 1
                or response.get("id") != identifier
                or type(response.get("revision")) is not int
                or response["revision"] != request["revision"]
                or type(response.get("ok")) is not bool):
            raise KernelError("CAD worker failed or returned an unmatched response")
        if not response.get("ok"):
            error = response.get("error", {})
            if not isinstance(error, dict):
                raise KernelError("CAD worker returned an invalid error")
            raise KernelError(error.get("message", "CAD operation failed"), error.get("code", "kernel_error"))
        if not isinstance(response.get("result"), dict):
            raise KernelError("CAD worker returned an invalid result")
        return response["result"]

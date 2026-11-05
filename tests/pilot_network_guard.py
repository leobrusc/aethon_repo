"""Opt-in whole-session Python network audit; no addresses or arguments logged."""
import json
import os
from pathlib import Path
import shlex
import sys

NETWORK = []
PROCESSES = []


def audit(event, args):
    if event in {"socket.connect", "socket.getaddrinfo", "socket.gethostbyname", "socket.gethostbyaddr"}:
        NETWORK.append(event)
        raise RuntimeError("Network prohibited in synthetic validation")
    if event == "subprocess.Popen":
        value = args[0]
        if value is None:
            command = args[1]
            tokens = shlex.split(command, posix=False) if isinstance(command, str) else command
            if not tokens: raise RuntimeError("Missing subprocess identity")
            value = os.fsdecode(tokens[0]).strip('"')
        executable = Path(os.fsdecode(value)).name.lower()
        if executable not in {"python", "python.exe", "python3", "python3.12", "git", "git.exe", "openssl", "openssl.exe", "powershell.exe", "pwsh.exe"}:
            raise RuntimeError("Unexpected subprocess in synthetic validation")
        PROCESSES.append(executable)


sys.addaudithook(audit)


def pytest_sessionfinish(session, exitstatus):
    target = os.environ.get("AETHON_OFFLINE_AUDIT_OUTPUT")
    if target:
        Path(target).write_text(json.dumps({"python_network_events": NETWORK,
            "allowed_local_process_basenames": PROCESSES, "status": "PASS" if not NETWORK else "FAIL",
            "scope": "Python audit events; native/child network isolation remains a separate operational gate"}, indent=2)+"\n", encoding="utf-8")
    if NETWORK: session.exitstatus = 1

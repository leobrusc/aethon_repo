"""Diagnostic observations only; never a persistence capability or authorization."""
from __future__ import annotations

import json
import os
from pathlib import Path
import stat
import subprocess

from aethon.prospective import fingerprint
from aethon.pilot_identity import path_identity


class CorruptCheckpoint(ValueError):
    pass


def safe_path(path, forbidden, directory=True):
    path = Path(path)
    if not path.is_absolute():
        raise ValueError("Absolute private path required")
    for component in [path, *path.parents]:
        info = component.lstat()
        if stat.S_ISLNK(info.st_mode) or getattr(info, "st_file_attributes", 0) & 0x400:
            raise ValueError("Symlink/reparse storage rejected")
    resolved = path.resolve(strict=True)
    if any(resolved == p or p in resolved.parents for p in map(Path.resolve, forbidden)):
        raise ValueError("Private destination is inside a repository/worktree")
    if directory and not resolved.is_dir():
        raise ValueError("Pre-provisioned private directory required")
    return resolved


def discover_repositories(root):
    """Includes externally located linked worktrees, not only .worktrees siblings."""
    common = os.fsdecode(subprocess.check_output(["git", "rev-parse", "--path-format=absolute", "--git-common-dir"], cwd=root)).rstrip("\r\n")
    entries = os.fsdecode(subprocess.check_output(["git", "worktree", "list", "--porcelain", "-z"], cwd=root))
    roots = [Path(common).parent, Path(common)]
    roots.extend(Path(line[9:]) for line in entries.split("\0") if line.startswith("worktree "))
    return sorted(set(p.resolve() for p in roots), key=str)


def probe_storage(path, forbidden, subject=None):
    """Never sets ACL, enables encryption, schedules deletion or creates roots."""
    path = safe_path(path, forbidden)
    identity = {"path_sha256": fingerprint(str(path)), "device": path.stat().st_dev, "inode": path.stat().st_ino,
                "path_identity": path_identity(path), "subject_sha256": fingerprint(subject) if subject else None}
    if os.name == "nt":
        script = r'''
$ErrorActionPreference='Stop'
$p=$env:AETHON_STORAGE_PROBE_PATH
$a=Get-Acl -LiteralPath $p
$sid=[System.Security.Principal.WindowsIdentity]::GetCurrent().User.Value
$owner=$a.GetOwner([System.Security.Principal.SecurityIdentifier]).Value
$rules=@($a.Access | ForEach-Object { @{sid=$_.IdentityReference.Translate([System.Security.Principal.SecurityIdentifier]).Value;type=$_.AccessControlType.ToString();rights=[int]$_.FileSystemRights} })
$v=Get-BitLockerVolume -MountPoint ([System.IO.Path]::GetPathRoot($p))
@{user=$sid;owner=$owner;protected=$a.AreAccessRulesProtected;rules=$rules;encryption=@{protection=$v.ProtectionStatus.ToString();status=$v.VolumeStatus.ToString();percent=$v.EncryptionPercentage}} | ConvertTo-Json -Depth 6 -Compress
'''
        try:
            shell = str(Path(os.environ.get("SystemRoot", "C:/Windows"))/"System32/WindowsPowerShell/v1.0/powershell.exe")
            p = subprocess.run([shell, "-NoProfile", "-NonInteractive", "-Command", script],
                               env={**os.environ, "AETHON_STORAGE_PROBE_PATH": str(path)}, capture_output=True, timeout=30)
            if p.returncode:
                raise ValueError("Observation unavailable")
            observation = json.loads(p.stdout)
            allowed = {observation["user"], "S-1-5-18", "S-1-5-32-544"}
            acl = (observation["owner"] == observation["user"] and observation["protected"] is True
                   and any(rule["type"] == "Allow" and rule["sid"] == observation["user"] and rule["rights"] & 7 == 7 for rule in observation["rules"])
                   and all(rule["sid"] in allowed for rule in observation["rules"] if rule["type"] == "Allow"))
            encrypted = observation["encryption"] == {"protection": "On", "status": "FullyEncrypted", "percent": 100}
            identity.update(acl="PASS" if acl else "PENDING", encryption="PASS" if encrypted else "PENDING", observation=observation)
        except (OSError, ValueError, KeyError, subprocess.TimeoutExpired):
            identity.update(acl="PENDING", encryption="PENDING", reason="native_observation_unavailable")
    else:
        info = path.stat()
        identity.update(acl="PASS" if info.st_uid == os.getuid() and stat.S_IMODE(info.st_mode) == 0o700 else "PENDING",
                        encryption="PENDING", reason="volume_encryption_not_independently_observed")
    if path_identity(path) != identity["path_identity"]:
        raise PermissionError("Storage changed during observation")
    # ACL/encryption observations are diagnostic, not an object-confined I/O lease.
    return {"status": "PENDING", "native_confinement": "NOT_AUDITED",
            "probe_fingerprint": fingerprint(identity), "observation": identity,
            "future_deletion": "NOT_AUDITED"}

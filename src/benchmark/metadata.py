"""Runtime metadata collection for reproducible experiments."""

from importlib.metadata import PackageNotFoundError, version
from pathlib import Path
from typing import Dict, Iterable
import platform
import socket
import subprocess
import sys


TRACKED_PACKAGES = (
    "numpy",
    "pandas",
    "scikit-learn",
    "transformers",
    "datasets",
    "openai",
)


def package_versions(packages: Iterable[str] = TRACKED_PACKAGES) -> Dict[str, str]:
    values = {}
    for package in packages:
        try:
            values[package] = version(package)
        except PackageNotFoundError:
            values[package] = "not-installed"
    return values


def git_revision(project_root: Path) -> str:
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=project_root,
            check=True,
            capture_output=True,
            text=True,
        )
        return result.stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        return "unavailable"


def environment_metadata(project_root: Path) -> dict:
    return {
        "host": socket.gethostname(),
        "platform": platform.platform(),
        "python_version": sys.version,
        "packages": package_versions(),
        "git_revision": git_revision(project_root),
    }

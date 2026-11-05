"""Identity observations, not a substitute for OS object-bound execution/I/O."""
from pathlib import Path
import stat

from aethon.pilot_governance import digest


def path_identity(path, *, file=False):
    path = Path(path)
    if not path.is_absolute():
        raise ValueError("Absolute identity path required")
    entries = []
    for item in [path, *path.parents]:
        info = item.lstat()
        if stat.S_ISLNK(info.st_mode) or getattr(info, "st_file_attributes", 0) & 0x400:
            raise ValueError("Link/reparse identity rejected")
        if item != path and not stat.S_ISDIR(info.st_mode):
            raise ValueError("Non-directory ancestor")
        entries.append({"path": str(item), "device": info.st_dev, "inode": info.st_ino,
                        "mode": info.st_mode, "uid": getattr(info, "st_uid", None),
                        "gid": getattr(info, "st_gid", None),
                        "attributes": getattr(info, "st_file_attributes", 0)})
    if file:
        info = path.stat()
        if not stat.S_ISREG(info.st_mode) or info.st_nlink != 1:
            raise ValueError("Single-link regular executable/dependency required")
        return {"ancestors": entries, "sha256": digest(path.read_bytes())}
    if not path.is_dir():
        raise ValueError("Directory identity required")
    return {"ancestors": entries}

import os
import sys
from pathlib import Path


DEFAULT_COMMAND = ["uvicorn", "main:app", "--host", "0.0.0.0"]


def resolve_command() -> list[str]:
    if len(sys.argv) > 1:
        return sys.argv[1:]

    return [*DEFAULT_COMMAND, "--port", os.environ.get("PORT", "4443")]


def resolve_target_identity(files_dir: Path) -> tuple[int, int]:
    uid_override = os.environ.get("RUN_AS_UID")
    gid_override = os.environ.get("RUN_AS_GID")

    if uid_override is not None or gid_override is not None:
        stat_result = files_dir.stat()
        uid = int(uid_override) if uid_override is not None else stat_result.st_uid
        gid = int(gid_override) if gid_override is not None else stat_result.st_gid
        return uid, gid

    stat_result = files_dir.stat()
    return stat_result.st_uid, stat_result.st_gid


def drop_privileges(uid: int, gid: int) -> None:
    if os.geteuid() != 0:
        return

    if uid == 0 and gid == 0:
        return

    os.setgid(gid)
    os.setuid(uid)


def main() -> None:
    files_dir = Path(os.environ.get("FILES_DIR", "/data"))
    files_dir.mkdir(parents=True, exist_ok=True)

    os.umask(int(os.environ.get("FILE_UMASK", "0002"), 8))

    target_uid, target_gid = resolve_target_identity(files_dir)
    drop_privileges(target_uid, target_gid)
    command = resolve_command()
    os.execvp(command[0], command)


if __name__ == "__main__":
    main()

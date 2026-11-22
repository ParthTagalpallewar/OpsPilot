"""Publish a frozen snapshot without replacing an existing capture."""

from pathlib import Path
from tempfile import NamedTemporaryFile


def publish_snapshot(path: Path, content: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with NamedTemporaryFile(dir=path.parent, delete=False) as stream:
        temporary = Path(stream.name)
        try:
            stream.write(content)
            stream.close()
            path.hardlink_to(temporary)
        finally:
            temporary.unlink(missing_ok=True)

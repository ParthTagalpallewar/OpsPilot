"""Flag control for the OpenTelemetry demo (flagd).

flagd reads this file (--uri file:./etc/flagd/demo.flagd.json) and reloads it
when it changes, so editing the JSON is enough to flip a flag.
"""
import json
import os
from pathlib import Path

DEFAULT_FLAG_FILE = (
    "/Users/parth/Development/AI Projects/opentelemetry-demo/src/flagd/demo.flagd.json"
)


def flag_file() -> Path:
    """Path of demo.flagd.json. Override with the OPSPILOT_FLAG_FILE env var."""
    return Path(os.environ.get("OPSPILOT_FLAG_FILE", DEFAULT_FLAG_FILE))


def _load(path: Path) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def get_flag(name: str) -> str:
    """Return the current defaultVariant of a flag."""
    data = _load(flag_file())
    if name not in data["flags"]:
        raise KeyError(f"Unknown flag: {name}")
    return data["flags"][name]["defaultVariant"]


def list_variants(name: str) -> list:
    """Return the variant names a flag offers."""
    data = _load(flag_file())
    if name not in data["flags"]:
        raise KeyError(f"Unknown flag: {name}")
    return list(data["flags"][name]["variants"].keys())


def set_flag(name: str, variant: str) -> str:
    """Set a flag's defaultVariant. Returns the previous variant.

    Raises KeyError for an unknown flag and ValueError for an unknown variant,
    before anything is written.
    """
    path = flag_file()
    data = _load(path)
    if name not in data["flags"]:
        raise KeyError(f"Unknown flag: {name}")
    flag = data["flags"][name]
    if variant not in flag["variants"]:
        raise ValueError(
            f"Variant {variant!r} not found for {name}. "
            f"Available: {list(flag['variants'].keys())}"
        )
    previous = flag["defaultVariant"]
    flag["defaultVariant"] = variant
    # Write in place (same file, same inode) so the Docker bind mount and the
    # flagd file watcher keep working. Do not use an atomic rename here.
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
        f.write("\n")
    return previous
from __future__ import annotations

import hashlib
import re
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

ASSETS = {
    Path("static/vendor/bootstrap/bootstrap.min.css"): {
        "url": "https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css",
        "marker": b"Bootstrap  v5.3.3",
        "minimum_size": 200_000,
    },
    Path("static/vendor/bootstrap/bootstrap.bundle.min.js"): {
        "url": "https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/js/bootstrap.bundle.min.js",
        "marker": b"Bootstrap v5.3.3",
        "minimum_size": 70_000,
    },
}


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def normalize(data: bytes) -> bytes:
    if data.startswith(b"\xef\xbb\xbf"):
        data = data[3:]
    data = re.sub(rb"/\*# sourceMappingURL=[^*]+\*/\s*$", b"", data)
    data = re.sub(rb"//# sourceMappingURL=.*?\s*$", b"", data)
    return data.rstrip() + b"\n"


def valid(data: bytes, marker: bytes, minimum_size: int) -> bool:
    return len(data) >= minimum_size and marker in data[:500]


def prepare(relative_path: Path, metadata: dict[str, object]) -> None:
    target = ROOT / relative_path
    marker = metadata["marker"]
    minimum_size = metadata["minimum_size"]

    if target.exists():
        existing = normalize(target.read_bytes())
        if valid(existing, marker, minimum_size):
            target.write_bytes(existing)
            print(f"OK {relative_path} sha256={sha256_bytes(existing)}")
            return

    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = target.with_suffix(target.suffix + ".download")
    request = urllib.request.Request(str(metadata["url"]), headers={"User-Agent": "NextToppersInventoryBuild/1.0"})
    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            data = normalize(response.read())
        if not valid(data, marker, minimum_size):
            raise RuntimeError(f"Downloaded file failed version/size verification for {relative_path}")
        temporary.write_bytes(data)
        temporary.replace(target)
        print(f"DOWNLOADED {relative_path} sha256={sha256_bytes(data)}")
    finally:
        temporary.unlink(missing_ok=True)


def main() -> int:
    for relative_path, metadata in ASSETS.items():
        prepare(relative_path, metadata)
    print("VENDOR_ASSETS_READY")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"VENDOR_ASSET_ERROR: {type(exc).__name__}: {exc}", file=sys.stderr)
        raise SystemExit(1)

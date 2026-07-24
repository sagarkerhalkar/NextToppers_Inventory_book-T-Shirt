from __future__ import annotations

import hashlib
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

ASSETS = {
    Path("static/vendor/bootstrap/bootstrap.min.css"): {
        "url": "https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css",
        "sha256": "9a821bde8fb0ae52535b0a318cdf1717a4da8a2cdffeec14d223d346a9348cd8",
    },
    Path("static/vendor/bootstrap/bootstrap.bundle.min.js"): {
        "url": "https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/js/bootstrap.bundle.min.js",
        "sha256": "c938e1227260834371896291dd5d28e98b5743ec952b721bdf791744ab06810d",
    },
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def prepare(relative_path: Path, metadata: dict[str, str]) -> None:
    target = ROOT / relative_path
    expected = metadata["sha256"]
    if target.exists() and sha256(target) == expected:
        print(f"OK {relative_path}")
        return

    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = target.with_suffix(target.suffix + ".download")
    request = urllib.request.Request(metadata["url"], headers={"User-Agent": "NextToppersInventoryBuild/1.0"})
    try:
        with urllib.request.urlopen(request, timeout=60) as response, temporary.open("wb") as output:
            output.write(response.read())
        actual = sha256(temporary)
        if actual != expected:
            raise RuntimeError(
                f"Checksum mismatch for {relative_path}: expected {expected}, received {actual}"
            )
        temporary.replace(target)
        print(f"DOWNLOADED {relative_path}")
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

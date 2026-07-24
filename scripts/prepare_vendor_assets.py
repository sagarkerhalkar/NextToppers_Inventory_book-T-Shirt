from __future__ import annotations

import hashlib
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

ASSETS = {
    Path("static/vendor/bootstrap/bootstrap.min.css"): {
        "url": "https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css",
        "sha256": "001fd1edbd9965625fba16c885b2429f5687683c25c30a5069ddc02fd79af949",
    },
    Path("static/vendor/bootstrap/bootstrap.bundle.min.js"): {
        "url": "https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/js/bootstrap.bundle.min.js",
        "sha256": "dbfea97d54111bd6f5364954df4fe8716a133c3309c517b80e2e16005f40790e",
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

from __future__ import annotations

import os
import sys
from pathlib import Path

APP_ROOT = Path(__file__).resolve().parent.parent
if str(APP_ROOT) not in sys.path:
    sys.path.insert(0, str(APP_ROOT))
os.chdir(APP_ROOT)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "nexttoppers_inventory.settings")

from waitress import serve  # noqa: E402
from nexttoppers_inventory.wsgi import application  # noqa: E402


if __name__ == "__main__":
    serve(
        application,
        host="127.0.0.1",
        port=3460,
        threads=8,
        channel_timeout=120,
        ident="NextToppersInventory",
    )

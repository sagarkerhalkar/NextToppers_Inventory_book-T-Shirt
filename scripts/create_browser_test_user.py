from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
os.chdir(ROOT)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "nexttoppers_inventory.settings")

import django

django.setup()

from inventory.models import User

EMPLOYEE_ID = os.getenv("BROWSER_SMOKE_EMPLOYEE_ID", "NXTTP9000")
PASSWORD = os.getenv("BROWSER_SMOKE_PASSWORD", "ReleaseTest1234")


def main() -> int:
    User.objects.filter(employee_id=EMPLOYEE_ID).delete()
    user = User.objects.create_user(
        employee_id=EMPLOYEE_ID,
        full_name="Release Browser Admin",
        mobile_number="+919876509000",
        password=PASSWORD,
        role=User.Role.SUPER_ADMIN,
        is_active=True,
        must_change_password=False,
    )
    print(f"BROWSER_TEST_USER_READY id={user.employee_id} pk={user.pk}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"BROWSER_TEST_USER_FAILED: {type(exc).__name__}: {exc}", file=sys.stderr)
        raise

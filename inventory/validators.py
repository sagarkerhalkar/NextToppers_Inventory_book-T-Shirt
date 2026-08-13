import re
from django.core.exceptions import ValidationError

EMPLOYEE_ID_PATTERN = re.compile(r"^NXTTP\d{4}$")
MOBILE_PATTERN = re.compile(r"^\+91[6-9]\d{9}$")
BOOK_ASSET_PATTERN = re.compile(r"^[A-Z0-9][A-Z0-9_-]{2,9}$")


def validate_employee_id(value):
    if not EMPLOYEE_ID_PATTERN.fullmatch(value or ""):
        raise ValidationError("Employee ID must be NXTTP followed by exactly four digits, for example NXTTP0043.")


def validate_indian_mobile(value):
    if not MOBILE_PATTERN.fullmatch(value or ""):
        raise ValidationError("Mobile number must be +91 followed by a valid 10-digit Indian mobile number.")


def validate_book_asset_id(value):
    if value and not BOOK_ASSET_PATTERN.fullmatch(value):
        raise ValidationError(
            "Book Asset ID must be 3 to 10 uppercase letters, numbers, hyphens or underscores, "
            "for example NTB-0001 or SCI9-001."
        )

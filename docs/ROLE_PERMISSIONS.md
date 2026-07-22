# Role Permissions

_Last updated: 22 July 2026_

This document records the confirmed role permissions for **Next Toppers Book and T-Shirt Inventory Management**.

## Super Admin

- Full application access.
- Can manage Super Admin, Admin and Staff accounts.
- Can manage role permissions.
- Can add, edit and delete Book Inventory records.
- Can add, edit and delete T-shirt Inventory records.
- Can download all available Excel and PDF reports.
- Can access audit logs and system settings.

## Admin

- Can add and edit Book Inventory records.
- Can add and edit T-shirt Inventory records.
- Can delete Book Inventory and T-shirt Inventory records.
- A confirmation step is required before deletion.
- Every deletion must be recorded in the audit log with the user, record details, date and time.
- Can download all available Excel and PDF reports.

## Staff

- Can add Book Inventory and T-shirt Inventory records when permitted.
- Can edit Book Inventory and T-shirt Inventory records when permitted.
- Cannot delete Book Inventory or T-shirt Inventory records.
- Delete buttons and delete APIs must be blocked for Staff accounts.
- Can download **all available Excel and PDF reports** for:
  - Book inventory
  - Book allocation and return history
  - T-shirt stock
  - T-shirt allocation history
  - User-wise T-shirt history
  - Logo-wise free, used, remaining, paid and total counts

## Security Rule

Permissions must be enforced in both the user interface and backend APIs. Hiding a button alone is not sufficient.

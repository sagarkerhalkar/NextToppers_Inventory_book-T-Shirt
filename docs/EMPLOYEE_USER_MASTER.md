# Employee and User Master

_Last updated: 22 July 2026_

This document records the confirmed employee/user master requirements for **Next Toppers Book and T-Shirt Inventory Management**.

## Confirmed Field

### Employee ID

- Every employee/user must have a unique Employee ID.
- Employee ID is mandatory.
- Duplicate Employee IDs must be blocked by both the user interface and backend validation.
- Employee ID will be used to identify the employee/user in Book allocation, Book return, T-shirt allocation, free-entitlement calculation, paid T-shirt history, reports, search and audit logs.
- Deactivating an account must not release or reuse its Employee ID.
- Historical records must continue to show the original Employee ID even after the employee/user is deactivated.

## Pending Decision

- Whether Employee ID will be entered manually or generated automatically by the application.
- Remaining employee/user master fields.

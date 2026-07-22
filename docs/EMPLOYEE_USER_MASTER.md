# Employee and User Master

_Last updated: 22 July 2026_

This document records the confirmed employee/user master requirements for **Next Toppers Book and T-Shirt Inventory Management**.

## Confirmed Field

### Employee ID

- Every employee/user must have a unique Employee ID.
- Employee ID is mandatory.
- Employee ID will be entered manually by an authorized Admin or Super Admin when the employee/user record is created.
- The application must not generate Employee IDs automatically.
- The confirmed Employee ID format is `NXTTP` followed by exactly four digits.
- Example: `NXTTP0043`.
- Valid pattern: `NXTTP0001` through `NXTTP9999`.
- Letters must be uppercase.
- Spaces, hyphens and other special characters are not allowed in the Employee ID.
- The user interface and backend must validate the format using the equivalent of `^NXTTP\d{4}$`.
- The entered Employee ID must be reviewed before the record is saved.
- Duplicate Employee IDs must be blocked by both the user interface and backend validation.
- Employee ID will be used to identify the employee/user in Book allocation, Book return, T-shirt allocation, free-entitlement calculation, paid T-shirt history, reports, search and audit logs.
- Deactivating an account must not release or reuse its Employee ID.
- Historical records must continue to show the original Employee ID even after the employee/user is deactivated.
- Creating or changing an Employee ID must be recorded in the audit log with the acting user, old value where applicable, new value, date and time.

## Pending Decisions

- Whether an Employee ID may be changed after the employee/user is created.
- Remaining employee/user master fields.

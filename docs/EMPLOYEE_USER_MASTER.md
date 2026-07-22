# Employee and User Master

_Last updated: 22 July 2026_

This document records the confirmed employee/user master requirements for **Next Toppers Book and T-Shirt Inventory Management**.

## Confirmed Fields

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
- The entered Employee ID must be reviewed before the employee/user record is saved.
- Duplicate Employee IDs must be blocked by both the user interface and backend validation.
- After the employee/user record is created, the Employee ID cannot be changed by Staff, Admin or Super Admin.
- The Employee ID field must become read-only after creation, and backend APIs must reject any later attempt to change it.
- A record created with an incorrect Employee ID must not be repaired by editing the ID. The incorrect record must be deactivated and a new correctly identified record must be created while preserving the original audit history.
- Employee ID will be used to identify the employee/user in Book allocation, Book return, T-shirt allocation, free-entitlement calculation, paid T-shirt history, reports, search and audit logs.
- Deactivating an account must not release or reuse its Employee ID.
- Historical records must continue to show the original Employee ID even after the employee/user is deactivated.
- Creating an Employee ID must be recorded in the audit log with the acting user, new Employee ID, date and time.
- Any rejected attempt to change an existing Employee ID must be recorded as a security event without changing the stored value.

### Employee Full Name

- Every employee/user must have a full name.
- Full name is mandatory when creating an employee/user record.
- A blank full name must be blocked by both the user interface and backend validation.
- The employee's full name must appear with the Employee ID in employee search, Book allocation and return records, T-shirt allocation and entitlement history, reports and audit records.

### Employee Mobile Number

- Every employee/user must have a mobile number.
- Mobile number is mandatory when creating an employee/user record.
- A blank or invalid mobile number must be blocked by both the user interface and backend validation.
- The final country-code and duplicate-number rules will follow the approved business decisions.
- Mobile numbers must be protected as personal data and displayed only to authorized users.

## Pending Decisions

- Remaining employee/user master fields and mobile-number validation rules.
- T-shirt entitlement period and approval workflow.
- Existing-data import, sample images and deployment details.

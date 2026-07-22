# Employee and User Master

_Last updated: 22 July 2026_

This document records the confirmed employee/user master requirements for **Next Toppers Book and T-Shirt Inventory Management**.

## 1. Employee ID

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
- Duplicate Employee IDs must be blocked by both the user interface and backend validation.
- After the employee/user record is created, the Employee ID cannot be changed by Staff, Admin or Super Admin.
- The Employee ID field must become read-only after creation, and backend APIs must reject any later attempt to change it.
- A record created with an incorrect Employee ID must be deactivated and a new correctly identified record must be created while preserving the original audit history.
- Deactivating an account must not release or reuse its Employee ID.
- Historical records must continue to show the original Employee ID.

## 2. Employee Full Name

- Every employee/user must have a full name.
- Full name is mandatory when creating an employee/user record.
- A blank full name must be blocked by both the user interface and backend validation.
- Full name must appear with the Employee ID in search, Book allocation and return records, T-shirt allocation and entitlement history, reports and audit records.

## 3. Employee Mobile Number

- Every employee/user must have a mobile number.
- Mobile number is mandatory.
- The supported format is Indian mobile format: country code `+91` followed by exactly 10 digits.
- The application may accept a 10-digit Indian number during entry but must store and display it in normalized `+91XXXXXXXXXX` format.
- Two employees cannot use the same mobile number.
- Duplicate mobile numbers must be blocked by both the user interface and backend validation.
- Mobile numbers must be protected as personal data and displayed only to authorized users.

## 4. Optional Employee Fields

The following employee fields are optional and must not block employee creation when left blank:

- Official email address
- Department
- Designation
- Joining date
- Office/location
- Employee profile picture

When an optional email address is supplied, the application must validate its format.

## 5. Default T-Shirt Size

- The employee profile must store a default T-shirt size.
- Supported sizes are `XS`, `S`, `M`, `L`, `XL`, `XXL` and `XXXL`.
- The stored size should automatically appear during T-shirt allocation but authorized users may confirm or change the allocation size for that transaction.
- A valid T-shirt size must be available before completing a T-shirt allocation.

## 6. Login and Password Recovery

- The login method is Employee ID plus password.
- Employees will not use self-service forgot-password recovery.
- When an employee forgets the password, an Admin or Super Admin must perform a secure password reset.
- The administrator must never be able to view the employee's existing password.
- A reset must create a temporary password or secure reset process.
- The affected employee must create a new password at the next sign-in.
- Password-reset actions must be recorded in the audit log, but no password may be stored in the audit log.

## 7. Audit and History

The audit log must record employee creation, activation, deactivation, role changes, profile changes, password resets and rejected Employee ID change attempts, including the acting user, affected employee, action, date and time.

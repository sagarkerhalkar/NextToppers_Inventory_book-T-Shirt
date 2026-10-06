# Employee and User Master

_Last updated: 23 July 2026_

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
- Admin and Super Admin may correct an Employee ID or Login User ID when it was entered by mistake.
- Correcting an ID must keep all Book, T-shirt and employee history linked to the same database record.
- Every ID correction must be recorded in the audit log.

## 2. Employee Full Name

- Every employee/user must have a full name.
- Full name is mandatory when creating an employee/user record.
- A blank full name must be blocked by both the user interface and backend validation.
- Full name must appear with the Employee ID in search, Book allocation and return records, T-shirt allocation and entitlement history, reports and audit records.

## 3. Employee Mobile Number

- Mobile number is optional for non-login Employee Master records.
- Leaving the Employee mobile number blank must not block creation, editing or Excel import.
- When a mobile number is entered, the supported format is Indian mobile format: country code `+91` followed by exactly 10 digits.
- Two Employee records cannot use the same supplied mobile number.
- Blank Employee mobile numbers may be used on multiple employee records.
- Login User mobile number remains mandatory and unique for account administration.
- Mobile numbers must be protected as personal data and displayed only to authorized users.

## 4. Optional Employee Fields

The following Employee Master fields are optional and must not block employee creation when left blank:

- Mobile number
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
- When a login user forgets the password, an Admin or Super Admin must perform a secure password reset.
- The administrator must never be able to view the user's existing password.
- A reset must create a temporary password or secure reset process.
- The affected user must create a new password at the next sign-in.
- Password-reset actions must be recorded in the audit log, but no password may be stored in the audit log.

## 7. Deletion and History Safety

- Admin and Super Admin can delete an Employee Master record that has no protected Book or T-shirt transaction history.
- An Employee with linked Book or T-shirt history cannot be permanently deleted and must be marked inactive instead.
- Admin and Super Admin can delete eligible Login Users subject to role permissions.
- A user cannot delete the account currently signed in.
- The last active Super Admin cannot be deleted.
- A Login User linked through protected legacy inventory history cannot be deleted and must be deactivated instead.

## 8. Audit and History

The audit log must record employee creation, ID corrections, deletion, activation, deactivation, role changes, profile changes and password resets, including the acting user, affected employee/user, action, date and time.

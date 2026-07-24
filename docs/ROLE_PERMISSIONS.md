# Role Permission Matrix

_Last updated: 23 July 2026_

This document records the confirmed role permissions for the **Next Toppers Book and T-Shirt Inventory Management** application. It forms part of the locked project requirements.

## Super Admin

The Super Admin has full authority over the application, including:

- Manage Super Admin, Admin and Staff accounts
- Create, edit, activate and deactivate accounts
- Correct Employee IDs and Login User IDs entered by mistake
- Delete eligible Employee Master and Login User records
- Assign or change roles
- Reset passwords through a secure reset process
- Manage role permissions
- Add, edit, delete, allocate and return inventory records
- Correct eligible Book Numbers/Asset IDs entered by mistake
- Access all Excel and PDF reports
- Access the complete audit log
- Manage all system and branding settings

Super Admin safeguards:

- The currently signed-in account cannot delete itself.
- The last active Super Admin cannot be deleted.
- Employees or Login Users with protected historical inventory links cannot be deleted and must be marked inactive instead.

## Admin

An Admin can:

- Add and edit Book Inventory and T-shirt Inventory records
- Correct Book Numbers/Asset IDs entered by mistake
- Delete eligible Book Inventory and T-shirt Inventory records after confirmation
- Allocate Books and T-shirts
- Receive returned Books and mark them **In Library**
- Download all available Excel and PDF reports
- Create, edit, activate and deactivate Staff accounts
- Correct Staff/Admin Login User IDs entered by mistake
- Delete eligible Staff and Admin Login User records
- Create, edit and delete eligible non-login Employee Master records
- Reset Staff passwords through a secure reset process
- Create other Admin accounts
- Edit other Admin account details
- Activate or deactivate other Admin accounts
- Reset other Admin passwords through a secure reset process
- Promote a Staff account to the Admin role
- Demote an Admin account to Staff when authorized
- Change the application logo
- Change the login-page background image
- Change the home-page image
- Change the organization/profile picture
- Preview and validate branding images before saving

Admin restrictions and safeguards:

- An Admin cannot create, edit, deactivate, reset, demote or delete a Super Admin account.
- An Admin cannot assign the Super Admin role.
- The currently signed-in account cannot delete itself.
- Employees or Login Users with protected historical inventory links cannot be deleted and must be deactivated instead.
- An Admin cannot view any user's existing password.
- Password resets must use a temporary password or secure reset process and require the affected user to create a new password at the next sign-in.
- At least one active Super Admin must always remain in the system.
- Account, ID correction, deletion, permission and branding changes must be recorded in the audit log.

## Staff

Staff can:

- Add Book Inventory and T-shirt Inventory records
- Edit Book Inventory and T-shirt Inventory records
- Allocate Books and T-shirts to users
- Receive returned Books and mark them **In Library**
- Download all available Excel and PDF reports for Book and T-shirt inventory
- Change their own profile picture, subject to image validation

Staff cannot:

- Delete Book Inventory records
- Delete T-shirt Inventory records
- Delete Employee Master or Login User records
- Create or manage user accounts
- Change roles or permissions
- Change the application logo, login background, home image or organization/profile picture
- Manage system-level settings unless separately approved

## Audit Requirements

The audit log must record all important actions, including:

- Record creation and editing
- Employee ID, Login User ID and Book Number corrections
- Employee and Login User deletion
- Book and T-shirt allocation
- Book returns
- Inventory deletion
- User-account creation and editing
- Account activation and deactivation
- Role changes
- Password-reset actions
- Application logo changes
- Login and home image changes
- Organization/profile picture changes

The audit log must include the acting user, affected user or inventory record, action, date and time. Passwords must never be stored in the audit log.

## Security Rule

Permissions must be enforced in both the user interface and backend APIs. Hiding a button alone is not sufficient.

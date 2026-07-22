# Next Toppers Book and T-Shirt Inventory Management — Locked Requirements

_Last updated: 22 July 2026_

These requirements are the approved baseline. New features may be added later, but the requirements below must not be removed, ignored or weakened without the owner's explicit approval.

## Official Application Name

**Next Toppers Book and T-Shirt Inventory Management**

## Branding and Images

The supplied Next Toppers group image will be used as the initial visual background for the login page and/or home page.

The supplied Next Toppers full logo will be used as the initial official application logo.

The application must include an authorized Branding Settings area where the permitted administrator can change, when required:

- Application logo
- Login page background image
- Home page image
- Organization/profile picture
- Individual user profile picture

Uploaded replacement images must be validated for supported file type and size, previewed before saving, and displayed responsively on mobile, tablet and desktop screens.

## User Roles

The application must support these three roles:

1. Super Admin
2. Admin
3. Staff

Access must use role-based access control so that every screen and action is permitted or blocked according to the signed-in user's role.

### Confirmed Staff Permissions

- Staff can add and edit Book Inventory and T-shirt Inventory records when permitted.
- Staff cannot delete Book Inventory or T-shirt Inventory records.
- Delete buttons and delete APIs must be blocked for Staff accounts.
- Staff can download all available Excel and PDF reports for Book and T-shirt inventory.
- Staff can allocate Books and T-shirts to users.
- Staff can receive returned books and mark them as **In Library**.
- Every Staff allocation or book-return action must update stock/status and be recorded in the audit log with the Staff user, recipient where applicable, item, quantity where applicable, return date where applicable, date and time.

### Confirmed Admin Permissions

- Admin can delete Book Inventory and T-shirt Inventory records.
- Admin deletion must be protected by a confirmation step.
- Each deletion must be recorded in the audit log with the Admin user, record type, record identifier, date and time.
- Admin can create Staff accounts.
- Admin can edit Staff account details.
- Admin can activate or deactivate Staff accounts.
- A deactivated Staff account cannot sign in, but its past inventory actions and audit history must remain available.
- Admin cannot create, edit, deactivate, promote or delete Super Admin accounts.
- Admin cannot give a Staff account the Admin or Super Admin role unless that permission is later explicitly approved.
- Every Staff-account creation, edit, activation and deactivation must be recorded in the audit log.

### Confirmed Super Admin Permissions

- Super Admin can delete records.
- Super Admin has authority over role and permission management.

The remaining detailed permissions for each role will be finalized separately.

## 1. Application Scope

The web application must manage two inventory categories:

1. Book Inventory
2. T-shirt Inventory

## 2. Book Inventory

Each book record must support:

- Book name
- Class name
- Stream name
- ISBN number
- Purchase date
- Bill number
- Bill photo
- Allocated to
- Allocation date
- Return date
- Current status:
  - Allocated
  - In Library

## 3. Book Photo Automation

When the user uploads or captures a book photo, the application should automatically identify and fill, wherever possible:

- ISBN number
- Book name
- Class

The remaining details will be entered manually by the user.

The user must be able to review and correct automatically detected information before saving.

## 4. Book Inventory Actions

Authorized users must be able to:

- Add book records
- Edit book records
- Delete book records, except Staff users
- Allocate books, including Staff users
- Receive returned books and mark them **In Library**, including Staff users
- Save the return date and clear or close the active allocation as applicable
- Download/export book data to Excel, including Staff users
- Download/export book data to PDF, including Staff users

Every book return must be recorded in the book history and audit log without deleting the earlier allocation history.

## 5. T-shirt Logo/Brand Master

The application must support editable T-shirt logo or brand names.

Initial examples:

- Next Toppers
- Nirmaan
- CUET

An administrator must be able to:

- Add a logo/brand
- Edit a logo/brand
- Delete a logo/brand
- Set the free annual quantity for each logo/brand

## 6. T-shirt Sizes

Supported sizes:

- XS
- S
- M
- L
- XL
- XXL
- XXXL

## 7. T-shirt Stock Inventory

Each stock record must support:

- Logo/brand name
- Size
- Number of T-shirts
- Available quantity
- Allocated quantity

## 8. T-shirt Allocation

The T-shirt allocation section must store:

- Allocated to
- Logo/brand
- Size
- Number of T-shirts allocated
- Allocation date
- Free or paid issue status

Staff, Admin and Super Admin can allocate T-shirts according to their confirmed permissions.

Each allocation must update stock automatically and appear in the user's full T-shirt history.

## 9. Annual Free T-shirt Entitlement

Each user has a configurable free T-shirt allowance for each logo/brand during a 12-month period.

Initial example rules:

- Next Toppers: 5 free T-shirts per user in 12 months
- CUET: 1 free T-shirt per user in 12 months
- Nirmaan: 5 free T-shirts per user in 12 months

These limits must be editable by an administrator.

The application must calculate and display for each user and logo:

- Free allowance
- Free quantity already used
- Free quantity remaining
- Paid quantity
- Total quantity received

## 10. Paid T-shirt Issue After Free Limit

After a user exhausts the free allowance for a logo within the 12-month period, any additional T-shirt requires purchase and HR approval.

The application must store:

- HR approval email attachment or approval proof
- Payment date
- T-shirt logo/brand
- T-shirt size
- Quantity
- User receiving the T-shirt
- Paid/approved status

The approved purchased T-shirt must then be added to the user's complete T-shirt allocation and purchase history.

## 11. T-shirt Administration and Reporting

Authorized users must be able to:

- Add records
- Edit records
- Delete records, except Staff users
- Allocate T-shirts, including Staff users
- Download/export all permitted data to Excel, including Staff users
- Download/export all permitted data to PDF, including Staff users
- View logo-wise free, used, remaining, paid and total counts
- View complete user-wise allocation and purchase history

## 12. Engineering and Quality Requirements

- All code must be tested.
- Automated tests must be included.
- GitHub Actions CI/CD must be included.
- The application must be optimized for major browsers.
- The application must work responsively on:
  - Android phones
  - iPhones
  - Tablets
  - iPads
  - Windows computers
  - macOS computers
  - Safari
  - Major modern desktop and mobile browsers

## 13. GitHub Delivery

Repository:

- Owner: sagarkerhalkar
- Repository: NextToppers_Inventory_book-T-Shirt

The complete source code, tests, documentation and CI/CD configuration must be maintained in this repository.

Approved future updates should be committed and pushed to the repository during active development work.

## 14. Pending Business Details

The following details are still to be collected before implementation decisions are finalized:

- Remaining detailed permissions for Super Admin, Admin and Staff
- Employee/user master fields
- Exact definition of the 12-month entitlement period
- HR approval workflow details
- Existing inventory Excel files, if any
- Sample book and bill photographs
- Deployment domain and hosting environment

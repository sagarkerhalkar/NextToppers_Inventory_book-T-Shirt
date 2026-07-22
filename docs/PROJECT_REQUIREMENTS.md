# Next Toppers Book and T-Shirt Inventory Management — Locked Requirements

_Last updated: 22 July 2026_

These requirements are the approved baseline. New features may be added later, but the requirements below must not be removed, ignored or weakened without the owner's explicit approval.

## Official Application Name

**Next Toppers Book and T-Shirt Inventory Management**

## Branding and Images

- The supplied Next Toppers group image will be used as the initial login-page and/or home-page background.
- The supplied Next Toppers full logo will be used as the initial application logo.
- Super Admin can manage all branding images.
- Admin can change the application logo, login background, home image and organization/profile picture.
- Staff cannot change organization-level branding.
- Staff can change their own optional profile picture.
- Replacement images must be validated for supported file type and size, previewed before saving and displayed responsively.
- Organization-level branding changes must be recorded in the audit log.

## User Roles and Permissions

The application must support:

1. Super Admin
2. Admin
3. Staff

Permissions must be enforced in both the user interface and backend APIs.

### Staff

- Can add and edit Book and T-shirt inventory records.
- Cannot delete Book or T-shirt inventory records.
- Can allocate Books and T-shirts.
- Can receive returned Books and mark them **In Library**.
- Can download all available Book and T-shirt Excel and PDF reports.
- Can change only their own profile picture.
- Cannot create or manage user accounts, roles, permissions or organization branding.

### Admin

- Has all operational inventory permissions.
- Can delete eligible Book and T-shirt records after confirmation.
- Can create, edit, activate, deactivate and reset passwords for Staff accounts.
- Can create, edit, activate, deactivate and reset passwords for other Admin accounts.
- Can promote Staff to Admin and demote Admin to Staff when authorized.
- Can change organization branding.
- Cannot create, edit, deactivate, reset, demote or delete Super Admin accounts.
- Cannot assign the Super Admin role.

### Super Admin

- Has full application access.
- Can manage Super Admin, Admin and Staff accounts.
- Can manage roles, permissions, system settings and branding.
- Can access all reports, backups and audit logs.

### Account Security

- User accounts must be deactivated rather than permanently deleted so their history remains available.
- Passwords must never be visible to administrators or stored in audit logs.
- Password resets must use a temporary password or secure reset process and require a new password at the next sign-in.
- All important account, role, password, inventory, branding and configuration actions must be audited.

## Employee and User Master

- Employee ID is mandatory, unique, entered manually and cannot be changed after creation.
- Employee ID format is `NXTTP` followed by exactly four digits, for example `NXTTP0043`.
- Full name is mandatory.
- Mobile number is mandatory and unique.
- Mobile format is `+91` followed by exactly 10 digits.
- Official email, department, designation, joining date, office/location and profile picture are optional.
- The employee profile must store a default T-shirt size.
- Login uses Employee ID plus password.
- There is no employee self-service forgot-password process; an Admin or Super Admin performs the reset.
- Detailed employee rules are maintained in `docs/EMPLOYEE_USER_MASTER.md`.

## 1. Application Scope

The application must manage:

1. Book Inventory
2. T-shirt Inventory
3. Employee/user master and access
4. Allocation, return, entitlement, approval, reporting, notification, backup and audit history

## 2. Book Inventory

Each physical Book must have its own unique Book Asset ID/barcode. The confirmed example format is `BOOK000001`.

Each Book record must support:

- Book Asset ID/barcode
- Book name
- Class name
- Stream name
- ISBN number
- Purchase date
- Bill number
- Bill photo
- Current condition: New, Good, Damaged or Lost
- Current status, including Allocated or In Library
- Allocated employee and Employee ID
- Allocation date
- Return date
- Return condition
- Return note
- Complete allocation and return history

### Book Photo Automation

When a Book photo is uploaded or captured, the application should identify and prefill, wherever possible:

- ISBN number
- Book name
- Class

The user must review and correct detected information before saving.

### Book Allocation and Return Rules

- Staff, Admin and Super Admin can allocate Books.
- A Book return due date is not required.
- The application will not create overdue-Book alerts.
- Book condition and a return note must be recorded during return.
- Returning a Book must close the active allocation while preserving earlier allocation history.
- Damaged and Lost Book records must remain in inventory history and must never be permanently deleted.
- All allocation, return, condition and status changes must be audited.

### Book Actions and Reports

Authorized users can add, edit, allocate, return, search, filter and export Book data.

- Staff cannot delete Book records.
- Admin and Super Admin can delete eligible records after confirmation, except protected Damaged/Lost history.
- All Staff, Admin and Super Admin users can download available Book reports in Excel and PDF.

## 3. T-Shirt Brand Master and Sizes

Initial brands:

- Next Toppers
- Nirmaan
- CUET

Authorized administrators can add, edit or delete brands and configure free-entitlement quantities.

Supported sizes:

- XS
- S
- M
- L
- XL
- XXL
- XXXL

## 4. T-Shirt Stock and Purchase Records

Each stock purchase must support:

- Brand/logo
- Size
- Purchase date
- Vendor
- Bill number
- Bill photo
- Purchased quantity
- Cost or total amount
- Available quantity
- Allocated quantity

Every stock change must preserve purchase and adjustment history.

## 5. T-Shirt Allocation

Each allocation must store:

- Employee ID and employee name
- Brand/logo
- Size
- Quantity
- Allocation date
- Free or paid issue status
- Acting Staff/Admin/Super Admin user

Rules:

- Staff, Admin and Super Admin can allocate T-shirts.
- Allocation must update stock automatically.
- Every allocation must appear in the employee's complete T-shirt history.
- An issued T-shirt cannot be returned to available stock.

## 6. Rolling 12-Month Free Entitlement

Free-entitlement calculation uses a **rolling previous 12-month period**, not a calendar year or joining-date year.

Initial configurable allowances:

- Next Toppers: 5 free T-shirts per employee in a rolling 12 months
- CUET: 1 free T-shirt per employee in a rolling 12 months
- Nirmaan: 5 free T-shirts per employee in a rolling 12 months

Rules:

- A new employee receives the full free allowance immediately.
- Unused allowance does not carry forward.
- Allowances remain configurable by authorized administrators.
- The application must show allowance, used quantity, remaining quantity, paid quantity and total received for each employee and brand.

## 7. Paid T-Shirt Issue After Free Limit

After the free limit is exhausted:

- A paid issue request is required.
- Admin or Super Admin can approve or reject the request.
- HR approval email/proof must be attachable and retained as part of the approval evidence.
- Payment amount and payment proof are mandatory.
- Stock must be deducted only after approval and payment proof are complete.
- The application must retain Pending, Approved and Rejected request history.
- Approved paid issues must appear in the employee's complete T-shirt allocation and purchase history.

Each request must store:

- Employee ID and name
- Brand/logo
- Size
- Quantity
- Payment amount
- Payment date
- Payment proof
- HR approval email/proof
- Request status
- Approver and approval date/time
- Rejection reason when rejected

## 8. Alerts, Imports and Notifications

### Low-Stock Alerts

- Book and T-shirt low-stock alerts are required.
- Alert thresholds must be configurable by authorized administrators.

### Excel Imports

- Bulk employee import through Excel is required.
- Bulk Book inventory import through Excel is required.
- Bulk T-shirt stock import through Excel is required.
- Imports must validate records, identify errors and prevent duplicate Employee IDs, mobile numbers, Book Asset IDs and other unique values.

### Notifications

Approval and allocation notifications are required through:

- In-app notifications
- Google Chat
- Email

Notification history and delivery status must be retained for authorized users.

## 9. Reporting and Exports

Available reports must support appropriate filters and Excel/PDF download, including:

- Book inventory
- Book allocation and return history
- Book condition and Lost/Damaged history
- T-shirt stock and purchase history
- T-shirt allocation history
- Employee-wise Book and T-shirt history
- Brand-wise free, used, remaining, paid and total counts
- Paid request status and payment history
- Low-stock status
- Audit history for authorized roles

Staff can download all available operational Book and T-shirt Excel/PDF reports. Sensitive administration and audit reports remain role-controlled.

## 10. Backup and Recovery

- Automatic daily database backup is required.
- Super Admin must be able to download a manual backup.
- Backup success or failure must be visible to Super Admin.
- Backup and restore actions must be audited.
- Restore must be protected by confirmation and authorized access.

## 11. Language and User Experience

- English is the primary application language.
- Hindi language support is required.
- The interface must be simple, responsive and usable on phones, tablets and computers.
- It must work on Android, iPhone, iPad, Windows, macOS, Safari and major modern browsers.

## 12. Engineering and Quality

- All code must be tested.
- Automated tests must be included.
- GitHub Actions CI/CD must be included.
- Role permissions must be tested at both UI and API levels.
- Import, backup, allocation, return, entitlement, approval and audit logic must have automated tests.
- Security validation must protect passwords and personal employee data.

## 13. GitHub Delivery

Repository:

- Owner: `sagarkerhalkar`
- Repository: `NextToppers_Inventory_book-T-Shirt`

Complete source code, tests, documentation and CI/CD configuration must be maintained in this repository.

## 14. Deployment Plan

- Initial deployment will be on a local Windows computer/server.
- Cloud deployment will be added later.
- The production domain will be decided later.
- The architecture and backup/export process must allow migration from the local Windows deployment to cloud hosting without losing data or history.

## 15. Remaining Implementation Inputs

The business choices above are confirmed. The following implementation inputs can be supplied during build or deployment:

- Existing employee, Book and T-shirt Excel data
- Sample Book and bill photographs
- Google Chat connection or space details
- Email/SMTP connection details
- Local Windows server specifications and backup destination
- Future cloud provider and production domain

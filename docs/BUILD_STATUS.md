# Build Status

## Initial working build

This branch introduces the first executable Django application for **Next Toppers Book and T-Shirt Inventory Management**.

Implemented foundation:

- Employee ID login with the confirmed `NXTTP0000` validation rule
- Super Admin, Admin and Staff roles
- Employee account creation, editing, activation/deactivation and administrator password reset
- Permanent Employee IDs and unique Indian mobile validation
- Book Asset ID generation using `BOOK000001`
- Book add/edit, allocation, return and protected history
- Book New/Good/Damaged/Lost conditions
- T-shirt brand/size stock, purchase history and low-stock indicators
- Rolling 12-month free entitlement calculation
- Paid T-shirt request, Admin/Super Admin approval/rejection and stock deduction after approval
- In-app, email and Google Chat notification logging
- Excel and PDF operational exports
- Branding settings
- Audit logging
- Windows setup, start and daily backup scripts
- Docker deployment files for later cloud migration
- Automated Django tests and GitHub Actions CI
- Responsive English-first interface with Django Hindi localization enabled

## Initial Windows port

The local application starts on port **3458**:

`http://localhost:3458`

## First setup

Open PowerShell inside the project folder and run:

```powershell
Set-ExecutionPolicy -Scope Process Bypass
.\scripts\setup_windows.ps1
.\scripts\start_windows.ps1
```

## Inputs still needed during deployment

- Initial logo and group background image binaries must be added to the repository/app media folder.
- Existing employee, Book and T-shirt Excel files.
- Google Chat webhook/space details.
- SMTP/email details.
- Local Windows server specifications and final backup drive/folder.
- Sample Book and bill photos for OCR calibration.

## Current validation note

The source files have been syntax-compiled locally. Full Django tests require installing dependencies; GitHub Actions performs that test after the branch is pushed.

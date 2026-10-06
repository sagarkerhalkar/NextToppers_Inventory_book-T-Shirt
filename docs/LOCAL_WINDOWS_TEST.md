# Local Windows Testing Guide

Use this guide to test **Next Toppers Book and T-Shirt Inventory Management** on a Windows 11 computer.

## Required software

Install **Python 3.12 (64-bit)** from python.org.

During installation, select:

- Add Python to PATH
- Install Python Launcher

Python 3.11 is also supported. Do not use Python 3.13 or 3.14 for this tested build.

## First installation

1. Extract the downloaded ZIP file.
2. Open the extracted application folder.
3. Double-click `INSTALL_LOCAL_TEST.bat`.
4. Wait while packages and the database are prepared.
5. Enter the first Super Admin details when requested:
   - Employee ID in `NXTTP0000` format
   - Full name
   - Mobile number in `+91XXXXXXXXXX` format
   - Optional email
   - Password of at least 4 characters
6. Wait for the message **INSTALLATION COMPLETED SUCCESSFULLY**.

Internet is required during the first installation because Python packages must be downloaded.

## Start the application

Double-click:

`START_LOCAL_TEST.bat`

The browser should open automatically at:

`http://localhost:3458`

Keep the server PowerShell window open while using the application.

## Stop the application

Double-click:

`STOP_LOCAL_TEST.bat`

## Verify installation

Double-click:

`VERIFY_LOCAL_TEST.bat`

It checks:

- Django configuration
- Database migrations
- Automated application tests
- Writable media, backup and static folders

## Test checklist

After login, test these actions:

1. Open the dashboard.
2. Create a Staff employee.
3. Add a Book.
4. Allocate the Book to the employee.
5. Return the Book with condition and return note.
6. Add T-shirt stock.
7. Issue a free T-shirt.
8. Open Reports and download Excel/PDF files.
9. Open Import Data and download an Excel template.
10. Upload a small test Excel file.

## Password rule

- Login passwords must contain at least 4 characters.
- Passwords remain securely hashed in the database.
- Existing passwords continue to work and are not changed by an application update.

## When an error appears

Do not close the error window immediately.

Take one clear screenshot showing the complete error and provide it in the project chat. Also mention which file you clicked and which step failed.

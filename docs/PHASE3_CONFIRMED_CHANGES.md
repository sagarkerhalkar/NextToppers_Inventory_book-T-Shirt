# Phase 3 — Confirmed Operational and UI Changes

_Last updated: 22 July 2026_

This document records the owner's confirmed changes after testing the local application.

## 1. Separate Employees from Login Access

- An employee record does not automatically require application login access.
- Ordinary employees can exist only as inventory recipients for Book and T-shirt transactions.
- Employees without login access must still appear in allocation, return, entitlement, history, search and reports.
- The organization may have only one data-entry login user or many data-entry login users.
- Super Admin must be able to decide which employee/account receives login access.
- Data-entry users must use role-based permissions for inventory entry, allocation, return, reports and administration.
- Login can be enabled or disabled without deleting the employee record or historical transactions.

## 2. Complete Book Allocation and Return Details

Every Book allocation must clearly show:

- Book Asset ID
- Book name
- Employee ID
- Employee full name
- Allocation date
- Allocation time
- Allocated by user
- Current allocation status
- Return date when returned
- Return time when returned
- Returned by user
- Return condition
- Return note

Additional requirements:

- The Book Inventory list must show the active allocation date/time and allocated employee when a Book is allocated.
- A Book history screen must show all previous allocations and returns.
- An employee-wise Book history screen must show all Books currently held and all previously returned Books.
- Allocation and return events must remain permanently available in reports and audit logs.

## 3. Employee-Wise Inventory Profile

Each employee must have one inventory profile/history page showing:

- Employee ID and full name
- Login enabled or disabled
- Current Books held
- Complete Book allocation and return history
- T-shirts received by brand, size, quantity and type
- Exact T-shirt issue date and time
- Free allowance, free used, free remaining and paid quantity for every brand
- Complete paid-request and approval history

Authorized users must be able to search an employee and open this combined history.

## 4. T-Shirt Brand and Entitlement Management

Authorized Admin and Super Admin users must be able to:

- Add a new T-shirt brand
- Edit a T-shirt brand name
- Activate or deactivate a brand
- Configure the free rolling-12-month allowance for each brand
- Preserve existing stock, allocation and history when a brand is renamed or deactivated

Initial brands must include:

- Next Toppers
- CUET
- Nirmaan
- Mission Jeet

The free quantity for every brand must be configurable from the application. It must not require a code change.

## 5. T-Shirt Stock and Allocation Details

The stock screen must provide brand and size-level management, including:

- Brand
- Size
- Available quantity
- Allocated quantity
- Total purchased quantity
- Low-stock threshold
- Low-stock status
- Edit action for authorized users
- Purchase-history access

Every T-shirt issue must show:

- Employee ID and name
- Brand
- Size
- Quantity
- Free or paid type
- Exact issue date and time
- Issued by user
- Approval status where applicable

## 6. Premium Global Inventory UI

The current basic table layout must be upgraded to a premium global inventory-system look.

Required design direction:

- Modern responsive dashboard
- Premium cards and information hierarchy
- Subtle 3D depth and glass-style surfaces
- Smooth hover, loading and page-entry animations
- Animated status badges and inventory counters
- Clear professional icons
- Better spacing and typography
- Responsive tables with mobile card view
- Clear timelines for allocation and return history
- Employee profile/history cards
- No excessive or distracting animation
- Fast performance on Windows, Android, iPhone, tablets, iPad, macOS and major browsers

## 7. Migration and Data Safety

- Existing local test data must remain usable after the upgrade.
- The current Super Admin account and inventory records must not be removed.
- Database migrations must preserve Book, stock and allocation history.
- Automated tests must cover login-disabled employees, multiple data-entry users, employee-wise histories, brand changes and exact transaction timestamps.

# Phase 4 — Smooth Performance and Periodic Reports

Confirmed requirements implemented:

- Teal (blue-green) and dark gray theme across the full application.
- Visible save progress and double-submit protection for every POST form.
- Windows local database/media relocation support so the active SQLite database is not continuously written inside a Google Drive synced folder.
- SQLite WAL, normal synchronous mode, connection reuse and busy timeout for smoother local saves.
- Separate Book activity reports in Excel and PDF.
- Separate T-shirt activity reports in Excel and PDF.
- Combined Book + T-shirt activity reports in Excel and PDF.
- Period options: current month, rolling 90 days, rolling 180 days, rolling 365 days, all history and custom start/end dates.
- Combined Excel reports use separate Summary, Book Activity and T-shirt Activity sheets.
- Automated date-filter report tests.

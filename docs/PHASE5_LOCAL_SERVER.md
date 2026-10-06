# Phase 5: Custom Asset IDs and LAN Server Access

## Custom Book Asset IDs

- A custom Asset ID can be entered while creating a Book.
- The value is optional. Leaving it blank keeps automatic IDs such as `BOOK000001`.
- Custom values use 3 to 10 uppercase letters, numbers, hyphens or underscores.
- Examples: `NTB-0001`, `SCI9-001`, `CUET-101`.
- Lowercase input is converted to uppercase.
- Duplicate Asset IDs are rejected.
- The Asset ID remains locked after Book creation so allocation and audit history cannot be disconnected.

## Typography

- The interface uses Plus Jakarta Sans with local system-font fallbacks.
- Headings, forms, navigation, tables and numeric fields use improved weights and spacing.
- The existing teal and dark-gray theme remains unchanged.

## Local Network Access

- The Windows server listens on `0.0.0.0:3458` with eight Waitress worker threads.
- `ENABLE_LAN_ACCESS.bat` opens Windows Firewall TCP port 3458.
- The setup adds detected local IPv4 addresses to Django allowed hosts and trusted origins.
- `START_LOCAL_TEST.bat` displays the exact URLs for this computer and other devices.
- Phones, tablets, iPads and computers must be connected to the same local network.
- A static IP or router DHCP reservation is recommended for a permanent server address.

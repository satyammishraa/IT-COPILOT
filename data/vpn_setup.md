# VPN Setup – Acme Corp

Acme uses **GlobalProtect** as its VPN client.

## Installation
1. Download GlobalProtect from the Company Portal app (Software > Network).
2. Portal address: **vpn.acme-internal.com**
3. Sign in with your Acme email and password, then approve the MFA prompt in Microsoft Authenticator.

## Common issues
- **VPN disconnects every few minutes:** switch the gateway from "Auto" to "India-BLR-01" or "US-East-02" in GlobalProtect settings.
- **"Portal not reachable":** check you are not on a hotel captive portal; open a browser first and accept the Wi-Fi terms.
- **MFA not arriving:** open Authenticator manually; notifications are sometimes delayed on Android battery saver.

VPN is mandatory for accessing SAP, SharePoint Admin and the HR portal from outside the office.
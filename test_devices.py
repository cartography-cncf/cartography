#!/usr/bin/env python3
"""
list_devices.py

Usage:
    python list_devices.py --key service-account.json --admin admin@yourdomain.com --customer C01234567

What it does:
 - Loads the service account JSON key
 - Uses domain-wide delegation (impersonates the admin user)
 - Calls Cloud Identity: GET https://cloudidentity.googleapis.com/v1/devices?customer=...
 - Paginates through results and prints JSON to stdout
"""

import argparse
import json
import sys
from google.oauth2 import service_account
from google.auth.transport.requests import AuthorizedSession

# Scopes: readonly is usually enough. Use broader scopes if you need to modify devices.
SCOPES = [
    "https://www.googleapis.com/auth/cloud-identity.devices.readonly",
    "https://www.googleapis.com/auth/admin.directory.user.readonly",
    "https://www.googleapis.com/auth/admin.directory.group.readonly",
    "https://www.googleapis.com/auth/admin.directory.group.member",
]

DEVICES_ENDPOINT = "https://cloudidentity.googleapis.com/v1/devices"
DEVICES_OWNED_ENDPOINT = "https://cloudidentity.googleapis.com/v1/devices/-/deviceUsers"

def make_delegated_session(sa_keyfile: str, admin_email: str, scopes=SCOPES):
    """
    Create an AuthorizedSession that will act as admin_email (domain-wide delegation).
    """
    # Load service account credentials from JSON key file and attach scopes
    creds = service_account.Credentials.from_service_account_file(sa_keyfile, scopes=scopes)
    # Create credentials that impersonate the admin user (domain-wide delegation)

    delegated = creds.with_subject(admin_email)
    return AuthorizedSession(delegated)

def list_devices(session: AuthorizedSession, customer: str, page_size: int = 100):
    """
    Generator that yields pages of devices as Python dicts.
    """
    params = {"customer": "customers/my_customer", "pageSize": page_size}
    next_token = None

    while True:
        if next_token:
            params["pageToken"] = next_token

        resp = session.get(DEVICES_ENDPOINT, params=params, timeout=30)
        if not resp.ok:
            # Print helpful debug and raise
            print(f"ERROR: status={resp.status_code} body={resp.text}", file=sys.stderr)
            resp.raise_for_status()

        data = resp.json()
        yield data

        next_token = data.get("nextPageToken")
        if not next_token:
            break

def list_owned_devices(session: AuthorizedSession, customer: str, page_size: int = 100):
    """
    Generator that yields pages of owned devices as Python dicts.
    """
    params = {"customer": "customers/my_customer", "pageSize": page_size}
    next_token = None

    while True:
        if next_token:
            params["pageToken"] = next_token

        resp = session.get(DEVICES_OWNED_ENDPOINT, params=params, timeout=30)
        if not resp.ok:
            # Print helpful debug and raise
            print(f"ERROR: status={resp.status_code} body={resp.text}", file=sys.stderr)
            resp.raise_for_status()

        data = resp.json()
        yield data

        next_token = data.get("nextPageToken")
        if not next_token:
            break

def main():
    parser = argparse.ArgumentParser(description="List Cloud Identity devices via service account impersonation.")
    parser.add_argument("--key", required=True, help="Path to service account JSON key file.")
    parser.add_argument("--admin", required=True, help="Admin email to impersonate (must be a Workspace admin).")
    parser.add_argument("--customer", required=True, help="Customer ID (format: C01234567).")
    parser.add_argument("--page-size", type=int, default=200, help="Page size (max 1000-ish depending on API).")
    args = parser.parse_args()

    sess = make_delegated_session(args.key, args.admin)
    all_devices = []
    for page in list_devices(sess, args.customer, page_size=args.page_size):
        devices = page.get("devices", [])
        all_devices.extend(devices)
        # optional: print progress
        print(f"Fetched {len(devices)} devices (total so far: {len(all_devices)})", file=sys.stderr)

    # Output final JSON
    print(json.dumps({"devices": all_devices}, indent=2))

    all_owned_devices = []
    for page in list_owned_devices(sess, args.customer, page_size=args.page_size):
        devices = page.get("deviceUsers", [])
        all_owned_devices.extend(devices)
        # optional: print progress
        print(f"Fetched {len(devices)} owned devices (total so far: {len(all_owned_devices)})", file=sys.stderr)
    
    # Output final JSON of owned devices
    print(json.dumps({"ownedDevices": all_owned_devices}, indent=2))

if __name__ == "__main__":
    main()

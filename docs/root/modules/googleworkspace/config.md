# Google Workspace Configuration

## Prerequisites

1. Create a project in the [Google Cloud Console](https://console.cloud.google.com/).
2. Enable the **Admin SDK API** and **Cloud Identity API**.
3. For domain-wide delegation, create a service account.
4. For OAuth, create an OAuth client ID with the application type
   **Desktop app**.

## Authentication

### Service account with domain-wide delegation

1. [Configure Google Workspace domain-wide delegation](https://developers.google.com/admin-sdk/directory/v1/guides/delegation)
   for the service account.
2. Download the service account credentials as a JSON file.
3. Set `GOOGLEWORKSPACE_GOOGLE_APPLICATION_CREDENTIALS` to the credential file
   path.
4. Set `GOOGLE_DELEGATED_ADMIN` to the delegated administrator email address.

### OAuth

Use the following helper to complete the OAuth flow and obtain a refresh token:

```python
from __future__ import print_function
import json
import os

from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build


scopes = [
    "https://www.googleapis.com/auth/admin.directory.customer.readonly",
    "https://www.googleapis.com/auth/admin.directory.user.readonly",
    "https://www.googleapis.com/auth/admin.directory.user.security",
    "https://www.googleapis.com/auth/cloud-identity.devices.readonly",
    "https://www.googleapis.com/auth/cloud-identity.groups.readonly"
]

print('Go to https://console.cloud.google.com/ > API & Services > Credentials and download secrets')
project_id = input('Provide your project ID:')
client_id = input('Provide your client ID:')
client_secret = input('Provide your client secret:')
with open('credentials.json', 'w', encoding='utf-8') as fc:
    data = {
        "installed": {
            "client_id": client_id,
            "project_id": project_id,
            "auth_uri":"https://accounts.google.com/o/oauth2/auth",
            "token_uri":"https://oauth2.googleapis.com/token",
            "auth_provider_x509_cert_url":"https://www.googleapis.com/oauth2/v1/certs",
            "client_secret":client_secret,
            "redirect_uris":["http://localhost"]
        }}
    json.dump(data, fc)
flow = InstalledAppFlow.from_client_secrets_file(
    'credentials.json', scopes)
flow.redirect_uri = 'http://localhost'
auth_url, _ = flow.authorization_url(prompt='consent')
print(f'Please go to this URL: {auth_url}')
code = input('Enter the authorization code: ')
flow.fetch_token(code=code)
creds = flow.credentials
print('Testing your credentials by getting the first 10 users in the domain ...')
service = build('admin', 'directory_v1', credentials=creds)
print('Getting the first 10 users in the domain')
results = service.users().list(customer='my_customer', maxResults=10,
                                orderBy='email').execute()
users = results.get('users', [])
if not users:
    print('No users in the domain.')
else:
    print('Users:')
    for user in users:
        print(u'{0} ({1})'.format(user['primaryEmail'],
                                    user['name']['fullName']))
print('Your credentials:')
print(json.dumps(creds.to_json(), indent=2))
os.remove('credentials.json')
```

Serialize the OAuth credentials as base64-encoded JSON:

```python
import base64
import json

auth_json = json.dumps({
    "client_id": "xxxxx.apps.googleusercontent.com",
    "client_secret": "ChangeMe",
    "refresh_token": "ChangeMe",
    "token_uri": "https://oauth2.googleapis.com/token",
})
print(base64.b64encode(auth_json.encode()).decode())
```

Store the output in an environment variable of your choice.

## Required Permissions

Configure domain-wide delegation or OAuth consent with these scopes:

- `https://www.googleapis.com/auth/admin.directory.customer.readonly`
- `https://www.googleapis.com/auth/admin.directory.user.readonly`
- `https://www.googleapis.com/auth/admin.directory.user.security`
- `https://www.googleapis.com/auth/cloud-identity.groups.readonly`

## Optional Permissions

Add `https://www.googleapis.com/auth/cloud-identity.devices.readonly` to enable
device sync. If Cloud Identity Premium is unavailable, omit this scope and
Cartography skips device sync.

Legacy domain-wide delegation configurations may also include
`https://www.googleapis.com/auth/cloud-platform`.

## Configure Cartography

For delegated service account authentication:

```bash
export GOOGLEWORKSPACE_GOOGLE_APPLICATION_CREDENTIALS="/path/to/credentials.json"
export GOOGLE_DELEGATED_ADMIN="admin@example.com"
```

For OAuth authentication:

```bash
export GOOGLEWORKSPACE_OAUTH_TOKENS="<base64-encoded-json>"
```

## Run Cartography

With delegated service account authentication:

```bash
cartography \
  --selected-modules googleworkspace \
  --googleworkspace-auth-method delegated \
  --googleworkspace-tokens-env-var GOOGLEWORKSPACE_GOOGLE_APPLICATION_CREDENTIALS
```

With OAuth authentication:

```bash
cartography \
  --selected-modules googleworkspace \
  --googleworkspace-auth-method oauth \
  --googleworkspace-tokens-env-var GOOGLEWORKSPACE_OAUTH_TOKENS
```

## Advanced Configuration

By default, Cartography requests all supported scopes. To use a subset, add a
`scopes` field to the OAuth JSON payload:

```python
import base64
import json

auth_json = json.dumps({
    "client_id": "xxxxx.apps.googleusercontent.com",
    "client_secret": "ChangeMe",
    "refresh_token": "ChangeMe",
    "token_uri": "https://oauth2.googleapis.com/token",
    "scopes": [
        "https://www.googleapis.com/auth/admin.directory.customer.readonly",
        "https://www.googleapis.com/auth/admin.directory.user.readonly",
        "https://www.googleapis.com/auth/admin.directory.user.security",
        "https://www.googleapis.com/auth/cloud-identity.groups.readonly",
    ],
})
print(base64.b64encode(auth_json.encode()).decode())
```

The `scopes` field is a Cartography-specific extension and is not part of the
standard Google OAuth token format.

When migrating from the deprecated `gsuite` module:

1. Update the environment variables:
   - `GSUITE_GOOGLE_APPLICATION_CREDENTIALS` -> `GOOGLEWORKSPACE_GOOGLE_APPLICATION_CREDENTIALS`
   - `GSUITE_DELEGATED_ADMIN` -> `GOOGLE_DELEGATED_ADMIN`
   - `GSUITE_TOKENS_ENV_VAR` -> `GOOGLEWORKSPACE_TOKENS_ENV_VAR`
   - `GSUITE_AUTH_METHOD` -> `GOOGLEWORKSPACE_AUTH_METHOD`
2. Enable the **Cloud Identity API** in addition to the Admin SDK API.
3. Add the scopes listed under **Required Permissions**.
4. Remove `https://www.googleapis.com/auth/admin.directory.group.readonly`,
   which is no longer needed.

## References

- [Google Cloud Console](https://console.cloud.google.com/)
- [Google Workspace domain-wide delegation](https://developers.google.com/admin-sdk/directory/v1/guides/delegation)

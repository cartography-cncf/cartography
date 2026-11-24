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

Authorize the OAuth flow as a Google Workspace administrator that can read
customer details, users, and user OAuth token metadata. A super administrator
is the simplest choice for validating the setup. A personal Google account or
a Workspace account without those privileges can complete OAuth consent but
will receive `403 Not Authorized to access this resource/api` from the Admin
Directory API.

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

Cartography uses `admin.directory.user.security` to sync the third-party OAuth
apps that users have authorized. Google offers no read-only scope for this data.
The scope also allows an administrator to revoke tokens and sign users out, but
Cartography only lists token metadata.

## Optional Permissions

With OAuth authentication, `admin.directory.user.security` is optional. Leave
it out of the `scopes` field described in
[Advanced Configuration](#advanced-configuration), and Cartography skips OAuth
app sync. Delegated and default authentication always request this scope, so
domain-wide delegation must authorize it.

Add `https://www.googleapis.com/auth/cloud-identity.devices.readonly` to enable
device sync. If Cloud Identity Premium is unavailable, omit this scope and
Cartography skips device sync.

Legacy domain-wide delegation configurations may also include
`https://www.googleapis.com/auth/cloud-platform`.

To sync standalone Apps Script projects, enable the **Google Drive API** and
**Apps Script API**, and authorize these three optional scopes for domain-wide
delegation:

- `https://www.googleapis.com/auth/drive.metadata.readonly`
- `https://www.googleapis.com/auth/script.projects.readonly`
- `https://www.googleapis.com/auth/script.deployments.readonly`

Apps Script sync runs only with service account credentials that can impersonate
users through domain-wide delegation: `delegated` authentication, or `default`
credentials that load such a service account key. OAuth user credentials skip
it. If the three scopes aren't delegated, Cartography skips Apps Script sync
without failing. When enabled, it makes at least one Drive `files.list` call for
each active user and two Apps Script calls (`projects.get` and
`projects.deployments.list`) for each standalone project, plus one more call
for each further page of scripts or deployments.

Each user must also turn on the Apps Script API in their own
[Apps Script settings](https://script.google.com/home/usersettings). Until they
do, Cartography can't read that user's projects and keeps the projects it
synced for that user earlier. Cleanup removes stale projects only of users whose
projects were all read; a project deleted between listing and reading does not
count against its owner. If the Drive API or Apps Script API is disabled in the
Google Cloud project, or a Google API returns an unexpected error, Cartography
skips Apps Script sync. Apps Script sync runs after the other Google Workspace
syncs, so an error in it does not skip them.

Cartography lists only scripts that a user owns in My Drive. Scripts in shared
drives and scripts bound to a Google Doc, Sheet, Slides, or Form aren't synced.

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

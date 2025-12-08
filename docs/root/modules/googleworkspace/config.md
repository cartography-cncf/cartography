## Google Workspace Configuration

This module allows authentication from a service account or via OAuth tokens.


### Create a Google Cloud Project and Service Account

1. Create an App on [Google Cloud Console](https://console.cloud.google.com/)
1. Enable the **Admin SDK API** for your project and the **Cloud Identity API**.
1. Create a Service Account

### Create credentials

#### Method 1: Using service account and domain-wide delegation (legacy)

1. [Perform Google Workspace Domain-Wide Delegation of Authority](https://developers.google.com/admin-sdk/directory/v1/guides/delegation) with following scopes:
    - `https://www.googleapis.com/auth/admin.directory.customer.readonly`
    - `https://www.googleapis.com/auth/admin.directory.user.readonly`
    - `https://www.googleapis.com/auth/admin.directory.user.security`
    - `https://www.googleapis.com/auth/cloud-identity.groups.readonly`
    - `https://www.googleapis.com/auth/cloud-identity.devices.readonly`
    - `https://www.googleapis.com/auth/cloud-platform`
1. Download the service account's credentials (JSON file).
1. Export the environmental variables:
    1. `GOOGLEWORKSPACE_GOOGLE_APPLICATION_CREDENTIALS` - location of the credentials file.
    1. `GOOGLE_DELEGATED_ADMIN` - email address that you created in step 2

#### Method 2: Using OAuth


1. Create an OAuth Client ID in the Google Cloud Console with application type "Desktop app".
1. Use helper script below for OAuth flow to obtain refresh_token
1. Serialize needed secret
    ```python
    import json
    import base64
    auth_json = json.dumps({"client_id":"xxxxx.apps.googleusercontent.com","client_secret":"ChangeMe", "refresh_token":"ChangeMe", "token_uri": "https://oauth2.googleapis.com/token"})
    base64.b64encode(auth_json.encode())
    ```
1. Populate an environment variable of your choice with the contents of the base64 output from the previous step.
1. Call the `cartography` CLI with `--googleworkspace-tokens-env-var YOUR_ENV_VAR_HERE` and `--googleworkspace-auth-method oauth`.




Google Oauth Helper :
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
print('Testing your credentials by gettings first 10 users in the domain ...')
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

### Migration from GSuite module

If you are migrating from the deprecated `gsuite` module, here are the key changes to configuration:

1. **Environment Variables**:
   - `GSUITE_GOOGLE_APPLICATION_CREDENTIALS` -> `GOOGLEWORKSPACE_GOOGLE_APPLICATION_CREDENTIALS`
   - `GSUITE_DELEGATED_ADMIN` -> `GOOGLE_DELEGATED_ADMIN`
   - `GSUITE_TOKENS_ENV_VAR` -> `GOOGLEWORKSPACE_TOKENS_ENV_VAR`
   - `GSUITE_AUTH_METHOD` -> `GOOGLEWORKSPACE_AUTH_METHOD`

2. **APIs**:
   - Ensure the **Cloud Identity API** is enabled in addition to the Admin SDK API.

3. **Scopes**:
   - The new module requires additional scopes. Ensure your service account or OAuth app has the following:
     - `https://www.googleapis.com/auth/admin.directory.customer.readonly` (New)
     - `https://www.googleapis.com/auth/admin.directory.user.readonly`
     - `https://www.googleapis.com/auth/admin.directory.user.security` (New)
     - `https://www.googleapis.com/auth/cloud-identity.groups.readonly` (New)
     - `https://www.googleapis.com/auth/cloud-identity.devices.readonly` (New)
     - `https://www.googleapis.com/auth/cloud-platform`
   - You can also delete the `https://www.googleapis.com/auth/admin.directory.group.readonly` scope that is no longer needed.

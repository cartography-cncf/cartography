## GSuite Configuration

This module allows authentication from a service account or via OAuth tokens.

### Method 1: Using service account (legacy)

Ingesting GSuite Users and Groups utilizes the [Google Admin SDK](https://developers.google.com/admin-sdk/).

1. [Enable Google API access](https://support.google.com/a/answer/60757?hl=en)
1. Create a new G Suite user account and accept the Terms of Service. This account will be used as the domain-wide delegated access.
1. [Perform G Suite Domain-Wide Delegation of Authority](https://developers.google.com/admin-sdk/directory/v1/guides/delegation)
1.  Download the service account's credentials
1.  Export the environmental variables:
    1. `CARTOGRAPHY_GSUITE__AUTH_METHOD` - `delegated`
    1. `CARTOGRAPHY_GSUITE__SETTINGS_ACCOUNT_FILE` - location of the credentials file.
    1. `CARTOGRAPHY_GSUITE__DELEGATED_ADMIN` - email address that you created in step 2

### Method 2: Using OAuth

1. Create an App on [Google Cloud Console](https://console.cloud.google.com/)
1. Refer to follow documentation if needed:
    1. https://developers.google.com/admin-sdk/directory/v1/quickstart/python
    1. https://developers.google.com/workspace/guides/get-started
    1. https://support.google.com/a/answer/7281227?hl=fr
1. Download credentials file
1. Export the environmental variables:
    1. `CARTOGRAPHY_GSUITE__AUTH_METHOD` - `oauth`
    1. `CARTOGRAPHY_GSUITE__CLIENT_ID`
    1. `CARTOGRAPHY_GSUITE__CLIENT_SECRET`
    1. `CARTOGRAPHY_GSUITE__REFRESH_TOKEN`
    1. `CARTOGRAPHY_GSUITE__TOKEN_URI` -

### Cartography Configuration

| **Name** | **Type** | **Description** |
|----------|----------|-----------------|
| **CARTOGRAPHY_GSUITE__AUTH_METHOD** | `str` | The auth method to use: `delegated` (legacy) or `oauth`. |
| **CARTOGRAPHY_GSUITE__DELEGATED_ADMIN** | `str` | The main of the delegated account. (for `delegated` auth only) |
| **CARTOGRAPHY_GSUITE__SETTINGS_ACCOUNT_FILE** | `path` | Path of the credential path. (for `delegated` auth only) |
| **CARTOGRAPHY_GSUITE__CLIENT_ID** | `str` | The Client ID to use to authenticate. (for `oauth` auth only) |
| **CARTOGRAPHY_GSUITE__CLIENT_SECRET** | `str` | The Client Secret to use to authenticate. (for `oauth` auth only) |
| **CARTOGRAPHY_GSUITE__REFRESH_TOKEN** | `str` | The refresh token to use to authenticate. (for `oauth` auth only) |
| **CARTOGRAPHY_GSUITE__TOKEN_URI** | `str` | The token URI to use to authenticate. (for `oauth` auth only) |

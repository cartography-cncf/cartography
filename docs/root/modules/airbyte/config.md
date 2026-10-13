# Airbyte Configuration

## Authentication

Create an application in the Airbyte admin panel. The application has the
permissions of the user who creates it.

Store its client secret in an environment variable. Pass the client ID with
`--airbyte-client-id` and the environment variable name with
`--airbyte-client-secret-env-var`.

## Required permissions

Cartography syncs every organization that the application's user belongs to.
The data it can collect depends on that user's roles:

| Data | Airbyte endpoints | Role needed in each organization |
| --- | --- | --- |
| Organizations, workspaces, sources, destinations, tags, connections | `GET /organizations`, `/workspaces`, `/sources`, `/destinations`, `/tags`, `/connections` | Read access to the workspaces, for example Workspace Reader |
| Users and their organization and workspace permissions | `GET /users`, `GET /permissions` | Organization Admin |

Listing users needs an organization role, and reading another user's
permissions needs Organization Admin. Airbyte returns workspace roles only for
the application's own user, so Cartography records workspace access for that
user alone. If Airbyte denies either request (HTTP
403) for an organization, Cartography logs a warning and still syncs that
organization's other resources and the remaining organizations. It does not
update or clean up that organization's users: users and access relationships
from an earlier sync are kept as they were. The sync ends with a warning that
lists the organizations without user data.

Any other error, such as a failed token request, an HTTP 401, 429 or 5xx, or a
403 from another endpoint, stops the Airbyte sync.

## Configure Cartography

For a self-hosted Airbyte instance, set its API base URL with
`--airbyte-api-url`. The default is `https://api.airbyte.com/v1`.

## Run Cartography

```bash
cartography \
  --selected-modules airbyte \
  --airbyte-client-id "$AIRBYTE_CLIENT_ID" \
  --airbyte-client-secret-env-var AIRBYTE_CLIENT_SECRET
```

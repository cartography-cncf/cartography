## Github Configuration

Follow these steps to analyze GitHub repos and other objects with Cartography.

1. Prepare your GitHub credentials.

    1. Make a GitHub user. Prepare a token on that user with the following scopes at minimum: `repo`, `read:org`, `read:user`, `user:email`

    1. For each GitHub instance you want to ingest, generate an API token as documented in the [API reference](https://developer.github.com/v3/auth/)
    1. Populate environment variables as defined bellow.

1. Call the `cartography` CLI

1. `cartography` will then load your graph with data from all the organizations you specified.

### Cartography Configuration

GitHub intel supports multiple instance, for each instance you must define following variables:

| **Name** | **Type** | **Description** |
|----------|----------|-----------------|
| **CARTOGRAPHY__GITHUB__{ORGNAME}__TOKEN** | `str` | The personnal access Token |
| **CARTOGRAPHY__GITHUB__{ORGNAME}__URL** | `str` | The GraphQL API URL (e.g. https://api.github.com/graphql). |

Example:
```
CARTOGRAPHY__GITHUB__FAKEORG__TOKEN="faketoken"
CARTOGRAPHY__GITHUB__FAKEORG__URL="https://api.github.com/graphql"
CARTOGRAPHY__GITHUB__OTHERORG__TOKEN="stillfake"
CARTOGRAPHY__GITHUB__OTHERORG__URL="https://github.example.com/api/graphql"
```

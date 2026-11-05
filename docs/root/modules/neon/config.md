# Neon Configuration

Cartography needs a Neon API key with read access to the organizations you want to inventory.

## Authentication

Neon has two kinds of API key, and both work. See [Manage API keys](https://neon.com/docs/manage/api-keys) for how to create one.

### Personal API key

A personal API key acts as your user and can see every organization you belong to. Without `--neon-org-ids`, Cartography syncs all of them.

### Organization API key

An organization API key belongs to one organization, not to a user. Pass that organization's ID with `--neon-org-ids`, because the endpoint that lists a user's organizations answers an error to an organization key. A project-scoped organization key can read only its one project and is not suitable for a full inventory.

## Required Permissions

| Access | Used for |
| --- | --- |
| Read projects, branches, compute endpoints, roles and databases | Core inventory. Failures here stop the sync |

## Optional Permissions

| Access | Feature it enables |
| --- | --- |
| Organization members | `NeonOrganizationMember` nodes and the `OWNED_BY` edge from API keys |
| Organization API keys | `NeonApiKey` nodes |
| Object storage buckets (Beta) | `NeonStorageBucket` nodes |
| Branch credentials (Beta) | `NeonCredential` nodes |

These listings answer `402`, `403` or `404` when the key or plan cannot read them. Cartography then logs a warning, keeps whatever nodes an earlier sync stored, and skips their cleanup. A read failure is not proof that the resources were deleted.

## Configure Cartography

| CLI option | Description |
| --- | --- |
| `--neon-api-key-env-var` | Name of the environment variable holding the Neon API key. Required to enable the module |
| `--neon-org-ids` | Comma-separated organization IDs (`org-...`) to sync. Required with an organization API key. Defaults to every organization a personal key's user belongs to |
| `--neon-base-url` | Neon API base URL. Defaults to `https://console.neon.tech/api/v2` |

## Run Cartography

```bash
export NEON_API_KEY="napi_..."
cartography \
  --neo4j-uri bolt://localhost:7687 \
  --selected-modules neon \
  --neon-api-key-env-var NEON_API_KEY
```

With an organization API key:

```bash
cartography \
  --neo4j-uri bolt://localhost:7687 \
  --selected-modules neon \
  --neon-api-key-env-var NEON_API_KEY \
  --neon-org-ids org-example-12345678
```

## Troubleshooting

- **The project listing is incomplete.** When the API reports `unavailable_project_ids`, Cartography loads the projects it did receive and skips project cleanup for that organization, so no project is deleted from the graph because of a slow response.
- **Rate limits.** The Neon API rate-limits requests per account. The module makes up to 5 requests per branch plus 2 per project, and retries `429` responses with exponential backoff.

## References

- [Neon API reference](https://api-docs.neon.tech/reference/getting-started-with-neon-api)
- [Neon Object Storage](https://neon.com/docs/storage/overview)
- [IP Allow](https://neon.com/docs/introduction/ip-allow)

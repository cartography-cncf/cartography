# Neon

The Neon module inventories [Neon](https://neon.com) serverless Postgres and Neon Object Storage through the [Neon API](https://api-docs.neon.tech/reference/getting-started-with-neon-api).

Tenancy has two levels. `NeonOrganization` is the root. Projects, organization members and API keys belong to an organization, and every other resource belongs to a project. `NeonOrganization` and `NeonProject` carry the `Tenant` ontology label.

| Area | Nodes | Ontology label |
| --- | --- | --- |
| Tenancy | `NeonOrganization`, `NeonProject` | `Tenant` |
| Identity | `NeonOrganizationMember` | `UserAccount` |
| Keys | `NeonApiKey`, `NeonCredential` | `APIKey` |
| Branching | `NeonBranch` | none |
| Compute | `NeonEndpoint` | none |
| Postgres | `NeonDatabase`, `NeonRole` | `Database` (databases only) |
| Object storage | `NeonStorageBucket` | `ObjectStorage` |

## Branches

A Neon branch is a copy-on-write clone of its parent, so a branch cut from production carries production data. Branches link to their parent with `BRANCHED_FROM`, and each branch `CONTAINS` its own roles, databases and storage buckets. Buckets branch with the database: a child branch serves its own copy of its parent's buckets from its own S3 endpoint, so the module records one `NeonStorageBucket` per branch.

## Internet exposure

`NeonEndpoint.exposed_internet` is `True` when any internet address may connect to the compute. The project's IP allowlist, `block_public_connections` and the compute's `disabled` flag all feed the verdict. An allowlist with `protected_branches_only` applies to protected branches only, so a preview branch's compute stays exposed even when the project looks locked down.

`NeonStorageBucket.exposed_internet` is `True` for `public_read` buckets. The `object_storage_public` rule reports them next to public S3, GCS, Azure, Scaleway, R2 and Supabase buckets.

## Secret handling

The module issues `GET` requests only, and stores no secret material:

- The role listing can include a role's password. Each role record is built from an explicit field list, so the password is dropped and never reaches the graph. The `reveal_password` endpoint is never called.
- Organization API keys are listed by id, name and usage. The API never returns the token itself.
- Branch credentials are listed by token id, scopes and usage. The listing never returns the API token or the S3 secret access key, and the `reveal` endpoint is never called.
- The connection URI endpoint is never called.

```{toctree}
config
schema
```

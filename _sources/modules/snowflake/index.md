# Snowflake

Cartography inventories a single Snowflake account: its identities and RBAC
model, its data hierarchy, its network access controls, and the integrations
that connect it to object storage and cloud IAM.

## Two Data Sources

The Snowflake REST API v2 covers most of the object inventory, but several
security-relevant surfaces exist only as SQL. Cartography reads both through the
same credential:

- The **object API** (`/api/v2/...`) provides accounts, users, roles, grants,
  warehouses, databases, schemas, tables, stages, external volumes, network
  policies, secrets, tasks, pipes, and the Snowpark Container Services objects.
- The **SQL API** (`POST /api/v2/statements`) provides what the object API omits:
  security and storage integrations, programmatic access tokens, MFA enrollment,
  account-level grants, shares and listings, replication and failover groups,
  resource monitors, and policy attachments.

No Snowflake driver is installed. Both surfaces are plain authenticated HTTP.

Surfaces that a given account cannot answer are skipped rather than failing the
sync, and a skipped surface also skips its own cleanup, so a missing privilege
or an edition limitation never deletes data Cartography previously collected.
Standard-edition accounts have no masking or row-access policies and no failover
groups; accounts without `ORGADMIN` cannot list sibling accounts in the
organization; `ACCOUNT_USAGE` views require `IMPORTED PRIVILEGES ON DATABASE
SNOWFLAKE` and lag real time by up to two hours.

## Shared Object Labels

Objects that can receive privileges through `GRANT` carry the shared
`SnowflakeSecurable` label. Grantees that can hold privileges carry the shared
`SnowflakePrincipal` label. Together they let a single `HAS_PRIVILEGE`
relationship connect any grantee to any grantable object, rather than needing one
relationship per label pair. Neither is a standalone node type.

## Identifiers

Snowflake object names are unique only within their own namespace and their own
object type: a stage, a pipe, a stream and a task can all be named `FOO` in one
schema, and a role and a warehouse can share a name at the account level. Node
ids are therefore account-scoped and type-tagged, of the form
`<ORG>.<ACCOUNT>/<object type>/<qualified name>`, for example
`MYORG.MYACCT/table/PROD.SALES.ORDERS`.

Because Snowflake folds unquoted identifiers to uppercase while preserving the
case of quoted ones, a name that is not a plain uppercase identifier stays
quoted inside the qualified name, as in `MYORG.MYACCT/schema/PROD."my schema"`.

## Cross-Provider Connections

Cartography links Snowflake to cloud resources that other modules already
ingested:

- External volume storage locations and external stages connect to `AWSS3Bucket`,
  `GCPBucket` and `AzureStorageAccount` nodes, and to the `AWSKMSKey` that
  encrypts them.
- Storage, API, catalog and notification integrations connect to the `AWSRole`
  they assume, and notification integrations and auto-ingest pipes connect to
  their `AWSSNSTopic`.

## Ontology Integration

Snowflake accounts are `Tenant`s, human users are `UserAccount`s and service
users are `ServiceAccount`s, roles of every kind are `PermissionRole`s,
databases are `Database`s, network policies and rules are
`NetworkAccessControl`s, external stages and external volume storage locations
are `ObjectStorage`, secrets are `Secret`s, programmatic access tokens are
`APIKey`s, and SAML / OAuth / SCIM security integrations are
`IdentityProvider`s. This makes Snowflake identities and grants comparable with
the equivalent AWS, Azure, GCP and Databricks structures.

```{toctree}
config
schema
```

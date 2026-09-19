# Snowflake Configuration

Cartography needs a Snowflake account identifier, a user, one credential, and a
warehouse to run SQL statements on.

## Prerequisites

### Service User and Warehouse

Create a dedicated service user and a warehouse for it. `TYPE = SERVICE` means
the user cannot log in interactively and cannot hold a password, which is what
you want for a collector:

```sql
USE ROLE USERADMIN;
CREATE USER CARTOGRAPHY_SVC TYPE = SERVICE
  COMMENT = 'Cartography inventory collector';

USE ROLE SYSADMIN;
CREATE WAREHOUSE CARTOGRAPHY_WH
  WAREHOUSE_SIZE = XSMALL AUTO_SUSPEND = 60 AUTO_RESUME = TRUE;
```

### Network Policy

Snowflake requires a network policy to be in effect for the user before it will
accept a programmatic access token. Key-pair authentication does not require one,
but restricting where the collector may connect from is worth doing either way.

Snowflake's guidance is that new policies use **network rules** rather than the
older `ALLOWED_IP_LIST` and `BLOCKED_IP_LIST` parameters. Create a rule holding
the addresses Cartography egresses from, then a policy that allows it:

```sql
USE ROLE SECURITYADMIN;

CREATE NETWORK RULE CARTOGRAPHY_EGRESS
  TYPE = IPV4
  MODE = INGRESS
  VALUE_LIST = ('198.51.100.10', '203.0.113.0/24')
  COMMENT = 'Addresses the Cartography collector connects from';

CREATE NETWORK POLICY CARTOGRAPHY_POLICY
  ALLOWED_NETWORK_RULE_LIST = ('CARTOGRAPHY_EGRESS')
  COMMENT = 'Restricts the Cartography service user to its collector hosts';
```

Attach it to the service user, not to the account, so it constrains only the
collector:

```sql
ALTER USER CARTOGRAPHY_SVC SET NETWORK_POLICY = CARTOGRAPHY_POLICY;
```

Verify what is actually in force:

```sql
SHOW PARAMETERS LIKE 'NETWORK_POLICY' IN USER CARTOGRAPHY_SVC;
```

Cartography ingests the policy and its rules as `SnowflakeNetworkPolicy` and
`SnowflakeNetworkRule` nodes, linked by `ALLOWS` and `BLOCKS`, with a
`GOVERNED_BY` edge from every user and account the policy applies to. So once
configured, the collector's own network restriction is visible in the graph
alongside everything else.

```{note}
Three details that cause surprises:

- **Precedence is most-specific-wins.** A policy on a security integration
  overrides one on a user, which overrides one on the account. Only one policy
  per level is active at a time, so attaching a policy to the user replaces any
  account-level policy for that user rather than adding to it.
- **Blocked beats allowed.** If an address appears in both lists, Snowflake
  applies the blocked list first.
- **You can lock yourself out.** Your own address must be in the allowed list, or
  activation fails. An empty policy denies every IPv4 address.
```

Creating a policy needs `SECURITYADMIN` or the global `CREATE NETWORK POLICY`
privilege. Attaching one to a user needs `OWNERSHIP` on the user plus `USAGE` on
the policy; attaching one to the whole account needs the global `ATTACH POLICY`
privilege.

If you need to run Cartography before a policy is in place, a token can carry a
time-limited exemption instead. This is for bootstrapping and testing only: it
expires, and until it does the token is usable from anywhere.

```sql
ALTER USER CARTOGRAPHY_SVC MODIFY PROGRAMMATIC ACCESS TOKEN CARTOGRAPHY_PAT
  SET MINS_TO_BYPASS_NETWORK_POLICY_REQUIREMENT = 60;
```

Cartography surfaces the remaining exemption on the
`SnowflakeProgrammaticAccessToken` node, so a token left exempt is auditable.

## Authentication

Snowflake's REST API does not accept passwords. Cartography supports the two
credential types Snowflake offers a machine identity. Key-pair is the stronger
choice: the private key never leaves your infrastructure, whereas a token is a
bearer secret that is replayable if it leaks.

### Key-Pair (JWT)

Generate an encrypted RSA key pair and register the public half on the user:

```bash
openssl genrsa 2048 | openssl pkcs8 -topk8 -v2 aes-256-cbc -inform PEM -out snowflake_key.p8
openssl rsa -in snowflake_key.p8 -pubout -out snowflake_key.pub
```

```sql
USE ROLE USERADMIN;
ALTER USER CARTOGRAPHY_SVC SET RSA_PUBLIC_KEY = '<contents of snowflake_key.pub, without the BEGIN/END lines>';
```

Put the PEM-encoded private key in one environment variable and its passphrase
in another. Cartography signs a short-lived assertion per sync and re-mints it
before Snowflake's one-hour ceiling.

### Programmatic Access Token

```sql
USE ROLE USERADMIN;
ALTER USER CARTOGRAPHY_SVC ADD PROGRAMMATIC ACCESS TOKEN CARTOGRAPHY_PAT
  ROLE_RESTRICTION = 'CARTOGRAPHY_RO'
  DAYS_TO_EXPIRY = 30;
```

Snowflake returns the secret once. Store it in an environment variable, keep the
expiry short, set `ROLE_RESTRICTION` so the token cannot be used with a more
privileged role, and revoke it when it is no longer needed.

## Required Permissions

The object API endpoints take no role parameter: they run as the user's **default
role**. So the role below must be set as the default role, not merely granted.

```sql
USE ROLE ACCOUNTADMIN;
CREATE ROLE CARTOGRAPHY_RO;
GRANT ROLE CARTOGRAPHY_RO TO USER CARTOGRAPHY_SVC;
ALTER USER CARTOGRAPHY_SVC SET DEFAULT_ROLE = CARTOGRAPHY_RO;

-- Run SQL statements.
GRANT USAGE ON WAREHOUSE CARTOGRAPHY_WH TO ROLE CARTOGRAPHY_RO;
-- Read the SNOWFLAKE.ACCOUNT_USAGE views: identities, grants, credential posture
-- and policy attachments. This is a read-only privilege.
GRANT IMPORTED PRIVILEGES ON DATABASE SNOWFLAKE TO ROLE CARTOGRAPHY_RO;
-- Account-level metadata: warehouses, resource monitors, parameters.
GRANT MONITOR ON ACCOUNT TO ROLE CARTOGRAPHY_RO;
-- Walk the data hierarchy.
GRANT USAGE ON ALL DATABASES IN ACCOUNT TO ROLE CARTOGRAPHY_RO;
GRANT USAGE ON ALL SCHEMAS IN ACCOUNT TO ROLE CARTOGRAPHY_RO;
GRANT REFERENCES ON ALL TABLES IN ACCOUNT TO ROLE CARTOGRAPHY_RO;
GRANT USAGE ON FUTURE SCHEMAS IN ACCOUNT TO ROLE CARTOGRAPHY_RO;
GRANT REFERENCES ON FUTURE TABLES IN ACCOUNT TO ROLE CARTOGRAPHY_RO;
```

This set is entirely read-only. With it, Cartography reads roles, database roles,
the role hierarchy and every grant from `SNOWFLAKE.ACCOUNT_USAGE`
(`ROLES`, `GRANTS_TO_ROLES` and `GRANTS_TO_USERS`), which lags real time by up to
two hours but requires no privilege that can modify anything.

`IMPORTED PRIVILEGES ON DATABASE SNOWFLAKE` is the one grant in that list you
should not drop. The object API and `SHOW ROLES` return only the roles the
collector's own role can see, and a partial answer is indistinguishable from a
complete one, so without the `ACCOUNT_USAGE` views Cartography cannot establish
that it saw every role. It then keeps the data it has and skips role, database
role and grant cleanup rather than risk deleting roles it merely could not see.
The graph stays correct, but stale roles are never removed.

## Optional Permissions

| Privilege | Enables | Cost of granting |
|---|---|---|
| `MANAGE GRANTS ON ACCOUNT` | Makes the object API and `SHOW GRANTS` account-wide, so roles and grants are current rather than up to two hours stale. | Not read-only: a role with `MANAGE GRANTS` can also grant and revoke privileges account-wide. Grant it only if the staleness matters more than the blast radius. |
| `MODIFY PROGRAMMATIC AUTHENTICATION METHODS` on a user | Listing that user's programmatic access tokens. Without it Cartography inventories only the tokens of the user it authenticates as, and reports the surface incomplete so no token is deleted at cleanup. A `USER` object has no plain `MODIFY` privilege, and no account-level privilege substitutes for this one. | Far from read-only: the same privilege grants creating, rotating and deleting that user's tokens and key pairs. There is no view-only equivalent, so the honest choice is usually to leave it ungranted and accept partial token coverage. |
| `ORGADMIN` | Listing the other accounts in the organization, so they appear as `SnowflakeAccount` nodes. | A highly privileged organization-level role. Usually not worth it; Cartography syncs the connected account either way. |

Cartography prefers the `ACCOUNT_USAGE` views for roles and grants and logs which
path it used. It falls back to the per-role object API only when those views are
unreadable; that path costs two requests per role and, as above, cannot establish
completeness, so the affected cleanups are skipped. Without `ORGADMIN`, only the
connected account is synced. Without `MODIFY PROGRAMMATIC AUTHENTICATION METHODS`
on a user, that user's programmatic access tokens are not listed. Every surface Snowflake refuses is skipped along with
its cleanup, so a missing privilege never deletes previously collected data.

## Configure Cartography

| Option | Description |
|---|---|
| `--snowflake-account` | Account identifier, `MYORG-MYACCOUNT` or `MYORG.MYACCOUNT`. |
| `--snowflake-user` | User to authenticate as. |
| `--snowflake-pat-env-var` | Environment variable holding the programmatic access token. |
| `--snowflake-private-key-env-var` | Environment variable holding the PEM-encoded RSA private key. |
| `--snowflake-private-key-passphrase-env-var` | Environment variable holding the key's passphrase. |
| `--snowflake-role` | Role used for SQL statements. Set it to the user's default role. |
| `--snowflake-warehouse` | Warehouse used to run SQL statements. |
| `--snowflake-databases` | Comma-separated databases to sync. Defaults to every readable database. |

Supply exactly one of `--snowflake-pat-env-var` or
`--snowflake-private-key-env-var`. Setting a passphrase without a private key is
a configuration error and fails loudly rather than silently skipping the module.

## Run Cartography

With a key pair:

```bash
cartography \
  --selected-modules snowflake \
  --snowflake-account MYORG-MYACCOUNT \
  --snowflake-user CARTOGRAPHY_SVC \
  --snowflake-private-key-env-var SNOWFLAKE_PRIVATE_KEY \
  --snowflake-private-key-passphrase-env-var SNOWFLAKE_PRIVATE_KEY_PASSPHRASE \
  --snowflake-role CARTOGRAPHY_RO \
  --snowflake-warehouse CARTOGRAPHY_WH
```

With a programmatic access token:

```bash
cartography \
  --selected-modules snowflake \
  --snowflake-account MYORG-MYACCOUNT \
  --snowflake-user CARTOGRAPHY_SVC \
  --snowflake-pat-env-var SNOWFLAKE_PAT \
  --snowflake-role CARTOGRAPHY_RO \
  --snowflake-warehouse CARTOGRAPHY_WH
```

## Advanced Configuration

Cartography syncs one account per run. To cover several accounts, run it once per
account; each account is a separate `SnowflakeAccount` tenant and its objects are
scoped to it, so the runs do not interfere.

On accounts with very many schemas, restrict the walk with
`--snowflake-databases`. The `SNOWFLAKE` and `SNOWFLAKE_SAMPLE_DATA` databases
and databases created from an inbound share are skipped automatically: they are
provider-managed and enumerating them is slow and usually unauthorized.

## Troubleshooting

**`390432 Network policy is required.`** The user has no network policy in effect,
which Snowflake requires before it will accept a programmatic access token.
Attach one as shown under Prerequisites, or use key-pair authentication, which
carries no such requirement. If the sync worked previously and then began failing
with this error, a `MINS_TO_BYPASS_NETWORK_POLICY_REQUIREMENT` exemption on the
token has expired.

**`390144 JWT token is invalid.`** The registered public key does not match the
private key in use, or the account identifier is wrong. Compare the fingerprint
Snowflake holds with the one your key produces:

```bash
snow sql -q "DESC USER CARTOGRAPHY_SVC" --format JSON | grep -i RSA_PUBLIC_KEY_FP
```

**Empty users, roles or grants.** The role lacks both `MANAGE GRANTS` and
`IMPORTED PRIVILEGES ON DATABASE SNOWFLAKE`, so neither the real-time nor the
`ACCOUNT_USAGE` path is readable. Grant the latter.

**Only one user's programmatic access tokens appear.** Listing another user's
tokens requires `MODIFY PROGRAMMATIC AUTHENTICATION METHODS` on that user, which no
account-level privilege implies.
The log names how many users could not be read, and the surface is reported
incomplete so the tokens already collected are not deleted.

**Objects missing from one database only.** The role has no `USAGE` on that
database or its schemas. Snowflake reports an unauthorized object identically to
a nonexistent one, so Cartography logs the skip rather than guessing.

## References

- [Snowflake REST APIs](https://docs.snowflake.com/en/developer-guide/snowflake-rest-api/snowflake-rest-api)
- [Authenticating to the REST API](https://docs.snowflake.com/en/developer-guide/snowflake-rest-api/authentication)
- [Programmatic access tokens](https://docs.snowflake.com/en/user-guide/programmatic-access-tokens)
- [Key-pair authentication](https://docs.snowflake.com/en/user-guide/key-pair-auth)
- [Network policies](https://docs.snowflake.com/en/user-guide/network-policies)
- [Network rules](https://docs.snowflake.com/en/user-guide/network-rules)
- [ACCOUNT_USAGE views](https://docs.snowflake.com/en/sql-reference/account-usage)

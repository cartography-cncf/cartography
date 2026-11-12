# 1Password Queries

A principal reaches a vault directly or through a group. Each grant is its own
`CAN_ACCESS` relationship, so these queries follow `MEMBER_OF` zero or one hops
to include both paths and report which one applies. `permissions` holds the
granted 1Password permission names. `manage_vault` and group ownership don't
imply `read_items`.

## Find Who Can Reveal Passwords in Each Vault

```cypher
MATCH (p)-[:MEMBER_OF*0..1]->(holder)-[grant:CAN_ACCESS]->(v:OnePasswordVault)
WHERE (p:OnePasswordUser OR p:OnePasswordServiceAccount)
  AND 'reveal_item_password' IN grant.permissions
RETURN v.id AS vault, coalesce(p.email, p.name, p.id) AS principal,
       CASE WHEN p = holder THEN 'direct' ELSE holder.name END AS via
ORDER BY vault, principal
```

## Find Suspended Users Who Still Hold Vault Access

```cypher
MATCH (u:OnePasswordUser)-[:MEMBER_OF*0..1]->(holder)-[grant:CAN_ACCESS]->(v:OnePasswordVault)
WHERE u.state <> 'ACTIVE'
RETURN u.email, u.state, v.id AS vault,
       CASE WHEN u = holder THEN 'direct' ELSE holder.name END AS via,
       grant.permissions
```

## Find Direct Grants That Bypass Groups

```cypher
MATCH (p)-[grant:CAN_ACCESS]->(v:OnePasswordVault)
WHERE p:OnePasswordUser OR p:OnePasswordServiceAccount
RETURN coalesce(p.email, p.name, p.id) AS principal, labels(p)[0] AS kind,
       v.id AS vault, grant.permissions
```

## Find Service Accounts That Can Read Items

```cypher
MATCH (sa:OnePasswordServiceAccount)-[:MEMBER_OF*0..1]->(holder)-[grant:CAN_ACCESS]->(v:OnePasswordVault)
WHERE 'read_items' IN grant.permissions
RETURN coalesce(sa.name, sa.id) AS service_account, v.id AS vault,
       CASE WHEN sa = holder THEN 'direct' ELSE holder.name END AS via
```

## Rank Vaults by How Many People Can Read Them

```cypher
MATCH (u:OnePasswordUser)-[:MEMBER_OF*0..1]->()-[grant:CAN_ACCESS]->(v:OnePasswordVault)
WHERE 'read_items' IN grant.permissions
RETURN v.id AS vault, v.name AS name, count(DISTINCT u) AS readers
ORDER BY readers DESC
```

## Find Credentials by Category and Who Can Read Them

```cypher
MATCH (v:OnePasswordVault)-[:CONTAINS]->(item:OnePasswordItem)
WHERE item.category IN ['API_CREDENTIAL', 'SSH_KEY']
  AND coalesce(item.state, '') <> 'ARCHIVED'
MATCH (p)-[:MEMBER_OF*0..1]->()-[grant:CAN_ACCESS]->(v)
WHERE (p:OnePasswordUser OR p:OnePasswordServiceAccount)
  AND 'read_items' IN grant.permissions
RETURN item.category, v.id AS vault, count(DISTINCT item) AS items,
       collect(DISTINCT coalesce(p.email, p.name, p.id)) AS readers
```

## Find Accounts With a Stale Snapshot

```cypher
MATCH (a:OnePasswordAccount)
WHERE duration.inDays(datetime(a.snapshot_collected_at), datetime()).days >= 2
RETURN a.id, a.snapshot_collected_at, a.collector_version
```

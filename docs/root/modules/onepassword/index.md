# 1Password

The 1Password module shows who can reach which vaults in a 1Password Business
account. It reads JSON snapshots that the open source
[1Password collector](https://github.com/subimagesec/collectors/tree/main/1password)
writes, so the 1Password service account token stays in your environment and
Cartography needs only read access to the snapshot.

```{toctree}
config
schema
```

## What Cartography ingests

- Users, guests, and service accounts, with their states
- Groups and group memberships
- The vaults in the collector's scope
- Direct user, service account, and group grants to those vaults, with
  permission names and the raw permission bitmask
- Item metadata, such as category, archive state, and timestamps

Snapshots never contain item fields or secret values. Vault names and item
titles appear only when the collector runs with `--include-titles`.

## Vault access

A principal can reach a vault directly or through one or more groups. Each
grant is a separate `CAN_ACCESS` relationship, so you can tell the paths
apart. The following query lists everyone who can reveal passwords in a vault,
and how:

```cypher
MATCH (p)-[:MEMBER_OF*0..1]->(holder)-[grant:CAN_ACCESS]->(v:OnePasswordVault)
WHERE (p:OnePasswordUser OR p:OnePasswordServiceAccount)
  AND 'reveal_item_password' IN grant.permissions
RETURN v.id AS vault, p.email AS principal,
       CASE WHEN p = holder THEN 'direct' ELSE holder.name END AS via
```

Group ownership and the `manage_vault` permission don't imply `read_items`.
1Password account policies and user states can also limit effective access.

## Snapshot lifecycle

Each snapshot covers one account and the vaults the collector was configured
to read. When a source holds several snapshots for the same account,
Cartography ingests only the most recently collected one. Nodes and
relationships that the snapshot no longer contains are deleted from that
account, so a revoked grant disappears on the next sync.

Cartography stops without changing the graph if any snapshot in the source is
incomplete, uses an unsupported schema version, or can't be read. An older
snapshot could otherwise restore access that 1Password already revoked.

The `snapshot_collected_at` property on `OnePasswordAccount` records when the
collector finished. A stale value means the collector stopped running, and the
graph shows access as of that time.

## Ontology

`OnePasswordUser` nodes carry the `UserAccount` label and link to canonical
`User` nodes by email. Users in the `SUSPENDED`, `PROVISION_SUSPENDED`, or
`DELETED` state are marked inactive. `OnePasswordServiceAccount` nodes carry
the `ServiceAccount` label, `OnePasswordGroup` nodes carry `UserGroup`, and
`OnePasswordItem` nodes carry `Secret`.

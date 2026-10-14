# BloodHound

The BloodHound module imports Active Directory data from
[BloodHound CE](https://github.com/SpecterOps/BloodHound) collector output.
Cartography does not query Active Directory itself: it reads the JSON files
that [SharpHound CE](https://github.com/SpecterOps/SharpHound) already
produced, from a local path or an object store.

See [configuration](config.md) for the supported input and how to run the
import, and the generated [schema](schema.md) for nodes, properties and
relationships.

```{toctree}
config
schema
```

## Graph model

Every AD object is keyed by its stable directory identifier, so later imports,
and other sources of AD data, update the same nodes:

| Node | BloodHound kind | Identifier | Ontology |
|---|---|---|---|
| `ADDomain` | `Domain` | Domain SID | `Tenant` |
| `ADUser` | `User` | SID | `UserAccount` |
| `ADGroup` | `Group` | SID | `UserGroup` |
| `ADComputer` | `Computer` | SID | Linked to a canonical `Device` by host name when the ontology module runs |
| `ADOU` | `OU` | GUID | |
| `ADGPO` | `GPO` | GUID | |
| `ADContainer` | `Container` | GUID | |

Every node also carries the `ADObject` label, the counterpart of BloodHound's
`Base`, and an `objectid` property equal to `id`. `ADDomain` is the tenant:
each object hangs off its domain through a `RESOURCE` relationship. Built-in
principals keep the domain-prefixed identifiers SharpHound emits, such as
`EXAMPLE.LOCAL-S-1-5-32-544` for the domain's Administrators group.

Object properties holding times, such as `whencreated` and
`lastlogontimestamp`, are stored as UTC datetimes; SharpHound's "never" values
are left empty.

`MEMBER_OF` includes primary group membership. Trust relationships run from
the trusting domain to the trusted domain, as in BloodHound CE:
`SAME_FOREST_TRUST` for `ParentChild`, `TreeRoot` and `CrossLink` trusts and
`CROSS_FOREST_TRUST` for every other trust type. A domain that only appears as
a trust target is kept as a placeholder `ADDomain` with `collected` set to
`false` until its own data is imported.

## Coming from BloodHound

The schema follows BloodHound CE's, adapted to Cartography's naming
conventions, so BloodHound queries translate mechanically:

- **Node labels** are the BloodHound kind prefixed with `AD`: `User` becomes
  `ADUser`, and `Base` becomes `ADObject`.
- **Relationship types** are the BloodHound edge name in UPPER_SNAKE, with
  acronyms kept whole: `MemberOf` becomes `MEMBER_OF` and `GPLink` becomes
  `GP_LINK`. Directions match BloodHound CE.
- **Properties** keep BloodHound's lowercase names (`objectid`, `name`,
  `domainsid`, `samaccountname`, `hasspn`, `enabled`, ...), except that times
  are datetimes rather than epoch seconds.

| BloodHound edge | Cartography relationship |
|---|---|
| `MemberOf` | `(:ADObject)-[:MEMBER_OF]->(:ADGroup)` |
| `Contains` | `(:ADObject)-[:CONTAINS]->(:ADObject)` |
| `GPLink` | `(:ADGPO)-[:GP_LINK]->(:ADObject)` |
| `SameForestTrust` | `(:ADDomain)-[:SAME_FOREST_TRUST]->(:ADDomain)` |
| `CrossForestTrust` | `(:ADDomain)-[:CROSS_FOREST_TRUST]->(:ADDomain)` |

This release imports the edges above. ACL, host-access and delegation edges
are not imported yet. Cartography does not compute BloodHound CE's Tier Zero
tags (`system_tags`, `highvalue`).

Example queries, BloodHound first, then Cartography:

Kerberoastable users:

```cypher
MATCH (u:User {hasspn: true, enabled: true}) RETURN u
```

```cypher
MATCH (u:ADUser {hasspn: true, enabled: true}) RETURN u
```

Everyone in Domain Admins, through nested groups:

```cypher
MATCH p = (n)-[:MemberOf*1..]->(g:Group) WHERE g.objectid ENDS WITH '-512' RETURN p
```

```cypher
MATCH p = (n:ADObject)-[:MEMBER_OF*1..]->(g:ADGroup) WHERE g.objectid ENDS WITH '-512' RETURN p
```

Computers a GPO applies to:

```cypher
MATCH p = (:GPO {name: $gpo})-[:GPLink]->()-[:Contains*1..]->(:Computer) RETURN p
```

```cypher
MATCH p = (:ADGPO {name: $gpo})-[:GP_LINK]->()-[:CONTAINS*1..]->(:ADComputer) RETURN p
```

Domain trusts:

```cypher
MATCH p = (:Domain)-[:SameForestTrust|CrossForestTrust]->(:Domain) RETURN p
```

```cypher
MATCH p = (:ADDomain)-[:SAME_FOREST_TRUST|CROSS_FOREST_TRUST]->(:ADDomain) RETURN p
```

Enabled users whose password is over a year old (times are datetimes, not
epoch seconds):

```cypher
MATCH (u:User {enabled: true})
WHERE u.pwdlastset < (datetime().epochseconds - 365 * 86400)
RETURN u
```

```cypher
MATCH (u:ADUser {enabled: true})
WHERE u.pwdlastset < datetime() - duration('P365D')
RETURN u
```

## Provenance

Every node and relationship read from collector output records where it came
from. Placeholder domains created for trust targets have none of these
properties.

- `source_uri`: the file it was read from. For a zip archive this is
  `<archive URI>!<member name>`.
- `collected_at`: when SharpHound collected it, taken from the timestamp prefix
  SharpHound puts on its file names and stored as an ISO 8601 string such as
  `2026-10-12T14:30:15`. SharpHound uses the collector host's local time with
  no time zone, so the value has no offset.
- `collector_version`: the SharpHound version.

## Import behavior

An import never deletes data unless it completes:

1. Every file is streamed and checked before anything is written. A truncated
   or malformed file, an unsupported format version, or missing domain data
   fails the import with an error that names the file, and nothing is written.
2. Nodes, then relationships, are written in batches. These writes are not one
   transaction: if a write fails part way, the rows already written stay, but
   nothing from the previous import is removed.
3. Stale data is removed only after every write succeeded, and only for the
   domains in the import. Importing one forest never removes another.

Clean-up also respects what SharpHound collected. Each relationship kind is
only cleaned up when the collection method that produces it ran (for example,
the trust relationships need the `Trusts` method) and the import holds every file type
that declares it (for example, `GP_LINK` needs `domains` and `ous`). A narrower SharpHound run, or an import missing a file, does not
delete relationships it did not look for.

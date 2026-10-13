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

| Node | Identifier | Ontology |
|---|---|---|
| `ADDomain` | Domain SID | `Tenant` |
| `ADUser` | SID | `UserAccount` |
| `ADGroup` | SID | `UserGroup` |
| `ADComputer` | SID | Linked to a canonical `Device` by host name |
| `ADOU` | GUID | |
| `ADGPO` | GUID | |
| `ADContainer` | GUID | |

Every node also carries the `ADObject` label. `ADDomain` is the tenant: each
object hangs off its domain through a `RESOURCE` relationship. Built-in
principals keep the domain-prefixed identifiers SharpHound emits, such as
`EXAMPLE.LOCAL-S-1-5-32-544` for the domain's Administrators group.

Each BloodHound edge kind becomes its own relationship type so that path
queries can follow specific abuse primitives:

| BloodHound edge | Cartography relationship |
|---|---|
| `MemberOf` | `(:ADObject)-[:MEMBER_OF]->(:ADGroup)` |
| `Contains` | `(:ADObject)-[:CONTAINS]->(:ADObject)` |
| `GPLink` | `(:ADGPO)-[:GP_LINK]->(:ADObject)` |
| `TrustedBy`, `SameForestTrust`, `CrossForestTrust` | `(:ADDomain)-[:TRUSTED_BY]->(:ADDomain)` |

`MEMBER_OF` includes primary group membership. `TRUSTED_BY` runs from the
trusted domain to the trusting domain, the direction in which access flows,
and records whether both domains are in the same forest. A domain that only
appears as a trust target is kept as a placeholder `ADDomain` with `collected`
set to `false` until its own data is imported.

## Provenance

Every node and relationship records where it came from:

- `source_uri`: the file it was read from. For a zip archive this is
  `<archive URI>!<member name>`.
- `collected_at`: when SharpHound collected it, taken from the timestamp prefix
  SharpHound puts on its file names. SharpHound writes the collector host's
  local time without a time zone, and Cartography stores it as written.
- `collector_version`: the SharpHound version.

## Import behavior

An import is all or nothing:

1. Every file is streamed and checked before anything is written. A truncated
   or malformed file, an unsupported format version, or missing domain data
   fails the import with an error that names the file.
2. Nodes, then relationships, are written in batches.
3. Stale data is removed only after the whole import succeeded, and only for
   the domains in the import. Importing one forest never removes another.

Clean-up also respects what SharpHound collected. Each relationship kind is
only cleaned up when the collection method that produces it ran (for example,
`TRUSTED_BY` needs the `Trusts` method), so a narrower SharpHound run does not
delete relationships it did not look for.

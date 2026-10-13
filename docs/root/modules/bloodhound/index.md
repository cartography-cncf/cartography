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
| `GenericAll` | `(:ADObject)-[:GENERIC_ALL]->(:ADObject)` |
| `GenericWrite` | `(:ADObject)-[:GENERIC_WRITE]->(:ADObject)` |
| `WriteDacl` | `(:ADObject)-[:WRITE_DACL]->(:ADObject)` |
| `WriteOwner` | `(:ADObject)-[:WRITE_OWNER]->(:ADObject)` |
| `Owns` | `(:ADObject)-[:OWNS]->(:ADObject)` |
| `ForceChangePassword` | `(:ADObject)-[:FORCE_CHANGE_PASSWORD]->(:ADObject)` |
| `AddMember` | `(:ADObject)-[:ADD_MEMBER]->(:ADObject)` |
| `AllExtendedRights` | `(:ADObject)-[:ALL_EXTENDED_RIGHTS]->(:ADObject)` |
| `AddKeyCredentialLink` | `(:ADObject)-[:ADD_KEY_CREDENTIAL_LINK]->(:ADObject)` |
| `ReadLAPSPassword` | `(:ADObject)-[:READ_LAPS_PASSWORD]->(:ADObject)` |
| `ReadGMSAPassword` | `(:ADObject)-[:READ_GMSA_PASSWORD]->(:ADObject)` |
| `AddSelf` | `(:ADObject)-[:ADD_SELF]->(:ADObject)` |
| `WriteSPN` | `(:ADObject)-[:WRITE_SPN]->(:ADObject)` |
| `DCSync` | `(:ADObject)-[:DC_SYNC]->(:ADDomain)` |
| `AdminTo` | `(:ADObject)-[:ADMIN_TO]->(:ADComputer)` |
| `CanRDP` | `(:ADObject)-[:CAN_RDP]->(:ADComputer)` |
| `CanPSRemote` | `(:ADObject)-[:CAN_PS_REMOTE]->(:ADComputer)` |
| `HasSession` | `(:ADComputer)-[:HAS_SESSION]->(:ADUser)` |
| `AllowedToDelegate` | `(:ADObject)-[:ALLOWED_TO_DELEGATE]->(:ADObject)` |
| `AllowedToAct` | `(:ADObject)-[:ALLOWED_TO_ACT]->(:ADComputer)` |
| `HasSIDHistory` | `(:ADObject)-[:HAS_SID_HISTORY]->(:ADObject)` |

Other BloodHound edges, including certificate services (ADCS), `ExecuteDCOM`,
`SQLAdmin` and edges BloodHound CE only computes in post-processing such as
`CoerceToTGT`, are not imported. Cartography does not compute BloodHound CE's
Tier Zero tags (`system_tags`, `highvalue`).

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

Shortest attack paths from enabled users to Domain Admins:

```cypher
MATCH p = shortestPath((u:User {enabled: true})-[:MemberOf|AdminTo|HasSession|GenericAll|GenericWrite|WriteDacl|WriteOwner|Owns|ForceChangePassword|AddMember|AllExtendedRights*1..]->(g:Group))
WHERE g.objectid ENDS WITH '-512'
RETURN p
```

```cypher
MATCH p = shortestPath((u:ADUser {enabled: true})-[:MEMBER_OF|ADMIN_TO|HAS_SESSION|GENERIC_ALL|GENERIC_WRITE|WRITE_DACL|WRITE_OWNER|OWNS|FORCE_CHANGE_PASSWORD|ADD_MEMBER|ALL_EXTENDED_RIGHTS*1..]->(g:ADGroup))
WHERE g.objectid ENDS WITH '-512'
RETURN p
```

Principals that can DCSync, directly or through group membership:

```cypher
MATCH p = (n)-[:MemberOf*0..]->()-[:DCSync]->(d:Domain) RETURN p
```

```cypher
MATCH p = (n:ADObject)-[:MEMBER_OF*0..]->()-[:DC_SYNC]->(d:ADDomain) RETURN p
```

Computers where Domain Admins have sessions:

```cypher
MATCH p = (c:Computer)-[:HasSession]->(u:User)-[:MemberOf*1..]->(g:Group)
WHERE g.objectid ENDS WITH '-512'
RETURN p
```

```cypher
MATCH p = (c:ADComputer)-[:HAS_SESSION]->(u:ADUser)-[:MEMBER_OF*1..]->(g:ADGroup)
WHERE g.objectid ENDS WITH '-512'
RETURN p
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
WHERE u.pwdlastset < (datetime().epochSeconds - 365 * 86400)
RETURN u
```

```cypher
MATCH (u:ADUser {enabled: true})
WHERE u.pwdlastset < datetime() - duration('P365D')
RETURN u
```

### Permission edges

Permission edges come from the access control entries (ACEs) SharpHound
collects on every object. Each ACE-derived edge carries `is_inherited`, which
is true only when every ACE granting the right was inherited from a parent
container; the derived `DC_SYNC` edge does not. Rights the
module does not import are counted in the sync log. An object's rights over
itself and ACEs granted to `OWNER RIGHTS` (`S-1-3-4`) produce no edge.

`OWNS` and `WRITE_OWNER` are imported as collected. BloodHound CE later drops
some of them in post-processing, when the domain enforces
`BlockOwnerImplicitRights` or `OWNER RIGHTS` ACEs limit what the owner can do;
Cartography does not.

`DC_SYNC` is derived when one principal holds both `GetChanges` and
`GetChangesAll` on the domain object. BloodHound CE also counts principals that
hold the two rights through different groups; Cartography only derives the
edge for a principal holding both, so follow `MEMBER_OF` to find its members.

### Host access edges

`ADMIN_TO`, `CAN_RDP` and `CAN_PS_REMOTE` come from the members of a computer's
local Administrators (RID 544), Remote Desktop Users (RID 555) and Remote
Management Users (RID 580) groups, as SharpHound read them from the computer
and as group policy assigns them to the computers it applies to. Local accounts
have no AD object and are skipped. When SharpHound collected the computer's user
rights, `CAN_RDP` also requires the remote interactive logon right, either held
by the Remote Desktop Users group or by the member itself. This applies to
members assigned by group policy too.

`HAS_SESSION` merges the session, privileged session and registry session
lists. Standalone `sessions` files are not imported.

### Placeholders

Edges often reference principals outside the import, for example a group from
a trusted domain named in an ACE. When SharpHound records the principal as a
user, group or computer, Cartography creates a placeholder `ADUser`, `ADGroup`
or `ADComputer` with `collected` set to `false`, keyed by the principal's SID,
as BloodHound CE does. Placeholders have no `RESOURCE` relationship and no
provenance. Importing the principal's own domain later fills in the same node
and sets `collected` to `true`, and a placeholder is removed once no
relationship references it.

## Provenance

Every node and relationship read from collector output records where it came
from. Placeholder domains and principals have none of these properties.

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
delete relationships it did not look for. Permission edges need the `ACL`
method; local group edges need `LocalAdmin`, `RDP` or `PSRemote`, or
`GPOLocalGroup`; `HAS_SESSION` needs `Session` or `LoggedOn`; delegation and
SID history edges need `ObjectProps`.

SharpHound cannot reach every computer. When a computer's output holds no
local group or session data, its existing host access edges of that kind are
kept rather than removed. For a computer SharpHound did reach, the local group
membership it read is authoritative: a group policy assignment that does not
show up in it is removed with the next import that collected local groups.

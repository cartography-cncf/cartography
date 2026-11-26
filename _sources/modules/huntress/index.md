# Huntress

The Huntress module ingests managed EDR inventory and detections from a Huntress
account: the account itself, the customer organizations under it, the agents
deployed on their endpoints, the incident reports the Huntress SOC raises, and
the users who have access to the console.

A Huntress account is the credential and billing boundary, and each customer it
protects is an organization underneath it. Both carry the `Tenant` label. The
account is the sub-resource owner of every other node, because that is the scope
an API credential can read; agents and incident reports additionally point at the
organization they belong to with `MEMBER_OF`.

`HuntressAgent` records the endpoint security posture Huntress reports: agent and
EDR versions, firewall status, EDR tamper protection (both the desired and the
last reported state), and the Managed Antivirus status of Microsoft Defender.

`HuntressIncidentReport` carries the `SecurityIssue` label. An incident points at
the agent it was raised on with `AFFECTS`, which the ontology propagates to the
canonical `Device`. Identity incidents, raised against a Microsoft 365 or Google
tenant rather than an endpoint, have no agent and therefore no `AFFECTS` edge.
Only the first ten remediations are inlined by the API, so the node keeps their
total count and the distinct types rather than a remediation list.

Huntress identifiers are unique across the platform, so nodes are keyed on the
raw API identifier. The one exception is `HuntressRole`: Huntress exposes no role
object, only a bare permission label on each membership, so a role is synthesized
as `<scope>/<account or organization ID>/<permission label>`. That keeps the same label
granted on the account and on an organization as two distinct grants. Roles carry
the `PermissionRole` label and users reach them through `HAS_ROLE`.

Huntress agents contribute data to canonical ontology `Device` nodes. Serial
number is the primary identity signal, with hostname used as a supplemental match
when both the Huntress and canonical hostnames are unique. Console users carry
the `UserAccount` label, so they are aggregated into canonical `User` nodes.

Listing memberships requires a permission that Huntress does not grant to every
API credential. When the credential cannot read them, the module logs a warning
and skips console users and roles rather than deleting the ones a previous run
ingested; every other resource still syncs.

See [configuration](config.md) for connection and ontology setup, and the
generated [schema](schema.md) for fields and relationships.

```{toctree}
config
schema
```

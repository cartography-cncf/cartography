# Zoom

The Zoom module inventories account users and their assigned Meetings plan type
using the account-wide Users API. It includes active users, deactivated users,
and pending invitations, plus the role IDs, group IDs, and login methods returned
in the user list. It makes no per-user API calls.

`ZoomAccount:Tenant` contains `ZoomUser:UserAccount` nodes through `RESOURCE`.
The user email, name, active status, and last-login timestamp populate the shared
ontology fields. Run the `ontology` module after `zoom` to correlate these users
with other providers through canonical `User` nodes and `HAS_ACCOUNT` edges.

Zoom does not return a user ID for pending invitations. Their graph IDs use the
account ID and normalized email; the next complete sync replaces an activated
invitation with the provider-ID user. User IDs are account-scoped so cleanup in
one account cannot delete another account's membership or invitation.

All three status lists must finish before ingestion and stale-user cleanup run.
An HTTP, pagination, or required-field error aborts the sync and retains existing
graph data. Requests retry rate limits and transient server errors, honor
`Retry-After` up to eight seconds per retry, and renew expiring OAuth tokens.
Creation and last-login timestamps are stored as native datetimes. Missing or
malformed optional timestamps are omitted; malformed values emit a warning
without blocking user ingestion or cleanup.

The assigned plan type is `1` (Basic), `2` (Licensed), `4` (Unassigned without
Meetings Basic), or legacy `99` (None, SSO creation only). This is user licensing
inventory; purchased seats, billing, add-on entitlements, detailed roles/groups,
meetings, recordings, and transcripts are outside this module's scope. Zoom's
last-login timestamp has a three-day reporting buffer.

```{toctree}
config
schema
```

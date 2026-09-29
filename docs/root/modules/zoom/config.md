# Zoom Configuration

Configure an account-level Server-to-Server OAuth app to inventory a Zoom account.

## Prerequisites

- A Zoom account owner or administrator who can create and activate a
  Server-to-Server OAuth app and assign its user-read scope.
- Access to the app's account ID, client ID, and client secret.

A Zoom Workplace Basic account can create this app and read its user inventory.
Zoom's user-management web portal may require a payment method on file before
you can manage additional users on a Basic account; this is separate from
authenticating the read-only connector.

## Authentication

1. Sign in to the [Zoom App Marketplace](https://marketplace.zoom.us/) with the
   account you want to inventory. In the current Marketplace interface, select
   **Developers**, then **+** → **Build app** on the **Created apps** page.
   First-time developers are prompted to review and accept the Marketplace
   Terms of Use and, separately, the API License and Terms of Use.
2. Select **Server to Server OAuth App**, click **Create**, enter an app name
   such as `Cartography`, and click **Create** again. This creates an account-level
   app for internal use; Marketplace publication and OAuth redirect URLs are not
   required.
3. On **App Credentials**, copy the **Account ID**, **Client ID**, and **Client
   Secret**. The account ID is the app's OAuth account identifier, not an email,
   vanity domain, or display account number.
4. On **Information**, use a short description such as
   `Read-only Zoom user inventory for Cartography`. Enter your organization's
   company name and the responsible administrator's name and monitored contact
   email. These fields save automatically.
5. Continue through **Feature** without enabling event subscriptions. The token
   on that page is for webhook verification; it is not the client secret or an
   API access token used by Cartography.
6. On **Scopes**, click **Add Scopes**, search for
   `user:read:list_users:admin`, select **View users** with that exact scope,
   and click **Done**. Leave the scope required, and describe how your deployment
   uses and stores user data in the scope-description field. For example:
   `Reads Zoom user profiles and assigned plan types to map account membership.
   Stores this metadata in our organization's Neo4j database for security inventory.`
   Adapt the description to your deployment's actual data handling.
7. On **Activation**, click **Activate your app**. Creating credentials or saving
   a scope alone does not activate the app. Confirm that Zoom displays
   **Your app is activated on the account**.

Cartography exchanges these credentials at `https://zoom.us/oauth/token` with
the `account_credentials` grant. Tokens last approximately one hour; Cartography
renews them automatically. You do not need to create or paste a bearer access
token, supply a refresh token, or complete an interactive login when running
Cartography.

## Required Permissions

| Granular OAuth scope | Read operation |
| --- | --- |
| `user:read:list_users:admin` | `GET /v2/users` for active, inactive, and pending users |

The older `user:read:admin` scope is also accepted by the endpoint, but the
granular scope above is sufficient for the default user inventory. Additional
inventories and their read scopes are listed below; no write scopes are required.

## Configure Cartography

| Option | Value |
| --- | --- |
| `--zoom-account-id` | Account ID from the OAuth app |
| `--zoom-client-id` | Client ID from the OAuth app |
| `--zoom-client-secret-env-var` | Name of the environment variable containing the secret; defaults to `ZOOM_CLIENT_SECRET` |

```bash
export ZOOM_CLIENT_SECRET='your-client-secret'
```

## Run Cartography

```bash
cartography \
  --neo4j-uri bolt://localhost:7687 \
  --selected-modules zoom,ontology \
  --ontology-users-source zoom \
  --zoom-account-id your-account-id \
  --zoom-client-id your-client-id
```

The example uses Zoom as the source for canonical `User` nodes in a standalone
test. For an existing graph, use your normal `--ontology-users-source` setting.

## Advanced Configuration

Run Cartography separately for each account using that account's OAuth app.
Cleanup is scoped to the configured account. This module targets Zoom's commercial
`zoom.us` service; Zoom for Government endpoints are not supported.

## Troubleshooting

- **400 from `/oauth/token`**: Verify the app's activation state and the Account
  ID from **App Credentials**. Zoom returns 400 when a deactivated
  Server-to-Server OAuth app attempts to obtain an access token.
- **401**: Check the credentials and app activation. An expired API token is
  renewed once automatically; repeated authorization failures abort the sync.
- **403 or insufficient scope**: Add `user:read:list_users:admin` to the active
  app and verify the app owner's permissions.
- **429**: Zoom's Users API has the `MEDIUM` rate-limit label. Requests retry
  up to three times, capping each `Retry-After` delay at eight seconds. A sustained
  rate limit on the user inventory aborts the sync without deleting prior users;
  on an optional section it preserves that section's data. Retry after the quota resets.
- **403 with code 2306 on meetings**: Zoom documents this when **Display
  meetings scheduled for others** is disabled in the account settings. The
  affected host's meetings are preserved; other hosts still refresh.
- **Incomplete/repeated pagination**: Retry the sync. Page tokens expire after
  15 minutes. Each status list has a safety limit of 10,000 pages; hitting it or
  receiving a truncated list aborts the sync before stale-user cleanup.

## References

- [Zoom Users API: List users](https://developers.zoom.us/docs/api/users/#tag/users/GET/users)
- [Zoom Users API specification](https://developers.zoom.us/api-hub/users/methods/endpoints.json)
- [Server-to-Server OAuth](https://developers.zoom.us/docs/internal-apps/s2s-oauth/)
- [OAuth scopes](https://developers.zoom.us/docs/integrations/oauth-scopes-overview/)
- [API rate limits](https://developers.zoom.us/docs/api/rest/rate-limits/)

## Optional inventories

The default sync still needs only the list-users scope. Enable additional
inventories with `--zoom-sections`, for example:

```bash
cartography --selected-modules zoom,ontology \
  --neo4j-uri bolt://localhost:7687 \
  --zoom-account-id "$ZOOM_ACCOUNT_ID" \
  --zoom-client-id "$ZOOM_CLIENT_ID" \
  --zoom-client-secret-env-var ZOOM_CLIENT_SECRET \
  --zoom-sections groups,roles,settings,apps,meetings,recordings,reports,dashboard,client_versions \
  --zoom-lookback-days 7
```

Add the scopes for the selected sections to the Server-to-Server OAuth app and
activate it. All scopes below are read-only; write scopes are unnecessary.

| Section | Additional scopes | Coverage and requirements |
| --- | --- | --- |
| `groups` | `group:read:list_groups:admin` | Pro or higher. Groups and memberships from the complete user inventory. |
| `roles` | `role:read:list_roles:admin`, `role:read:role:admin` | Pro or higher. Common account roles, their privileges and group restrictions; primary user roles come from the user inventory. Select `groups` to link privilege restrictions to groups. |
| `settings` | `account:read:settings:admin`, `account:read:lock_settings:admin`, `group:read:list_groups:admin`, `group:read:settings:admin`, `group:read:lock_settings:admin`, `user:read:settings:admin` | Paid account. Account, group and user security controls, including account and group lock flags, private chat, recording auto-delete, waiting-room scope, and the account's 2FA group/role lists and inactivity sign-out periods. |
| `apps` | `marketplace:read:list_apps:admin`, `marketplace:read:app:admin` | Account-added and approved Marketplace apps, their developer type, and exact OAuth scope identifiers. This does not enumerate individual user installations, account-created apps or restricted apps. |
| `meetings` | `meeting:read:list_meetings:admin`, `meeting:read:meeting:admin` | Unexpired scheduled meetings and recurring series of Basic/Licensed users. Instant meetings and per-occurrence exceptions are not included. |
| `recordings` | `cloud_recording:read:list_user_recordings:admin`, `cloud_recording:read:recording_settings:admin` | Pro or higher with cloud recording enabled. Active Licensed users' recorded meeting instances and sharing/protection controls. The app's authorizing role must allow viewing recording content to read these settings. |
| `reports` | `report:read:user_activities:admin`, `report:read:operation_logs:admin`, `report:read:meeting_activity_log:admin` | Pro or higher. Sign-in/out, administrative, and meeting audit metadata. Meeting audit trails must be enabled by Zoom Support. |
| `dashboard` | `dashboard:read:list_meetings:admin`, `dashboard:read:list_meeting_participants:admin` | Business or higher. Past meeting instances, including single-participant meetings, with participant device category, client version and operating system where Zoom returns them. |
| `client_versions` | `dashboard:read:client_versions:admin` | Business or higher with the Dashboard enabled. One account-wide count per client version; counts are not attributed to users or devices. |

Settings are separate `configured` and `locked` snapshots. Locked values describe
whether users can change a control; they are not enabled/disabled policy values.
The connector does not calculate effective policy inheritance. Fields absent from
a successful response remain unknown rather than being interpreted as disabled.
Meeting and recording passcodes become protection flags; passwords, access URLs,
media, transcripts, and free-form audit details are not stored.

`--zoom-lookback-days` accepts 1–30 UTC calendar days (default 7) for recordings,
reports, and dashboard data. The current day is included, and requests are split
at month boundaries. Each successful scan replaces that section's rolling window;
older events and recordings leave the graph. This is not a historical archive.
The scheduled-meeting inventory is independent of this lookback.

Zoom limits dashboard queries to the last six months and report/recording queries
to monthly ranges. Data may arrive late. Participant identities and device fields
may be withheld for external users; participant rows are observations, not a
persistent device inventory. `ZoomUser.last_client_version` is the last login
client reported by the Users API, not every client used by the account.

Per-owner and per-item reads use at most four workers, each with its own HTTP
session, pooled across all owners of a section. Settings use up to five reads per
account, four per user/group, and two per locked account/group snapshot; all
readable snapshots are written in one batch. Pagination is capped at 10,000 pages.

`--zoom-request-limit` (default 100,000) caps logical GET requests per sync, and
`--zoom-heavy-request-limit` (default 10,000) caps report and dashboard requests,
which Zoom counts toward a daily limit shared by every app on the account. These
are Cartography safeguards, not Zoom quotas. Each request keeps the client's
three-retry limit. An optional section that reaches a limit, or is still rate
limited after retries, stops further reads for that section, keeps its unread
snapshots, and lets independent sections continue. The required user inventory
still fails on a limit or sustained rate limit.

A denied optional endpoint emits a warning and retains the affected snapshot.
A recording whose sharing settings are still processing preserves its host's
prior recording snapshot until a later sync; other hosts still refresh and prune.
Meetings and recordings belong to the account and link to their current host with
`HOSTED_BY`. A stale meeting or recording is removed only when its last known host
was read completely, or when that host is absent from the complete user
inventory. A transfer keeps the resource identity and only the new host
relationship. A resource moved to a host that cannot be read while its previous
host is readable cannot be distinguished from a deletion and is removed until the
new host is read. Documented not-found responses for a single meeting, role, app or
settings owner affect only that item. If the dashboard reports a listed meeting
as invalid or not yet ended, the whole dashboard snapshot is kept until a later
complete read. Existing recordings also remain when their
owner becomes inactive or loses a Licensed seat. Meetings are likewise preserved
for pending users and users without a Basic/Licensed seat. Cleanup resumes after a
successful read or removes the snapshot when the owner leaves the account. Successful independent sections and owners
can still refresh. Credential failures,
server errors, and incomplete pagination fail explicitly. Stale cleanup requires
a complete read for the relevant account, owner, or report. Review warnings as well
as the process exit status when assessing coverage.

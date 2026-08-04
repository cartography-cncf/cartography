# Anthropic Configuration

The Anthropic module supports two authentication methods: a static Admin API key, or
Workload Identity Federation. Federation is recommended: it involves no long-lived
secret, and it reaches endpoints that Admin API keys are refused on.

## Option 1: Admin API key

Create an Admin API key in the
[Anthropic Console](https://console.anthropic.com/settings/admin-keys) and store it in
an environment variable. Pass the name of that variable with
`--anthropic-apikey-env-var`.

```bash
cartography \
  --selected-modules anthropic \
  --anthropic-apikey-env-var ANTHROPIC_API_KEY
```

An Admin API key covers organization members, workspaces, workspace members and API
keys. It is rejected with a 403 on service accounts, federation issuers and federation
rules, so those resources will not appear in the graph.

## Option 2: Workload Identity Federation

Cartography presents the OIDC token that its own platform issues (a Kubernetes
projected service account token, a GitHub Actions identity token) and exchanges it for
a short-lived Anthropic access token. Nothing long-lived is stored.

### Prerequisites

Set these up once in the Anthropic Console:

1. A **service account** with `organization_role: admin`.
2. A **federation issuer** registered for your identity provider.
3. A **federation rule** with `oauth_scope: org:admin` targeting that service account.
   This rule must be created in the Console. Granting a workload organization-admin
   access is a deliberate human action, and the API will not let automation bootstrap
   it.

Note the rule's `subject_prefix` matcher. A trailing `*` is a prefix match, so a
GitHub Actions rule like `repo:my-org/my-repo:*` also matches `pull_request` runs,
including ones triggered from forks: anyone who can open a pull request against the
repository could then mint an `org:admin` token. Pin the prefix to a specific ref, for
example `repo:my-org/my-repo:ref:refs/heads/main`.

### Configure Cartography

Point cartography at the identity token and at the three ids that identify the
exchange. The token is read fresh on every exchange, so a projected token that rotates
on disk is always current.

```bash
cartography \
  --selected-modules anthropic \
  --anthropic-identity-token-file /var/run/secrets/anthropic/token \
  --anthropic-federation-rule-id fdrl_xxx \
  --anthropic-organization-id 00000000-0000-0000-0000-000000000000 \
  --anthropic-service-account-id svac_xxx
```

Use `--anthropic-identity-token-env-var` instead of `--anthropic-identity-token-file`
when the identity token arrives in an environment variable rather than on disk. Pass the
name of the variable, not the token itself. The two are mutually exclusive.

If both an Admin API key and a federation configuration are supplied, cartography uses
federation and logs a warning. A federation configuration missing one of its three ids
is treated as an operator mistake and fails loudly rather than silently falling back.

### Per-workspace resources

Skills, agents, environments, deployments, vaults and memory stores are scoped to a
workspace and have no organization-wide listing. An `org:admin` token cannot reach
them, and there is no way to downscope one: the token endpoint accepts only the
`jwt-bearer` grant, so each workspace needs its own exchange.

Set up a second federation rule to ingest them:

1. Create a rule with `oauth_scope: workspace:developer` and
   `applies_to_all_workspaces: true`. One rule covers every workspace; cartography
   varies the workspace on each exchange.
2. Add its target service account as an explicit member of every workspace you want
   covered. Enabling a rule for a workspace does not create that membership, and
   `applies_to_all_workspaces` does not either. Every service account is implicitly a
   member of the default workspace only.

Then pass the rule with `--anthropic-workspace-federation-rule-id`, alongside the
`org:admin` configuration above. Without it, cartography syncs the organization plane
and logs that it is skipping the rest.

Cartography never writes, so it will not add those workspace memberships for you even
though the Admin API can.

A workspace whose exchange fails is skipped with a warning and the sync continues.
Consider giving the workspace rule its own federation issuer with `check_jti: false`:
otherwise, replay protection can reject the second and later exchanges when your
identity token carries a `jti` and does not rotate between them. A dedicated issuer
also keeps it updatable through the API, which an issuer backing an `org:admin` rule
is not.

### Troubleshooting

Every credential-level rejection from the token exchange returns an opaque
`400 invalid_grant`; the specific cause is only logged on Anthropic's side. The
Console's authentication history page
(`platform.claude.com/settings/workload-identity-federation?tab=history`) shows which
validation step failed.

Two causes worth checking first:

- **Replay protection.** A federation issuer's `check_jti` defaults to `true`, which
  makes each assertion carrying a `jti` claim single-use. Kubernetes projected tokens
  carry one.
- **Workspace membership.** For rules enabled on more than the default workspace, the
  target service account must be an explicit member of the workspace being requested.
  Enabling a rule for a workspace does not create that membership.

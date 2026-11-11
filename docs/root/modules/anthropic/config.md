# Anthropic Configuration

Cartography authenticates to the Anthropic Admin API with either an Admin API
key or workload identity federation. Pick one.

## Option 1: Admin API key

Claude Console organizations: create an Admin API key in the
[Claude Console](https://platform.claude.com/settings/admin-keys). Console admin
keys carry full Admin API access.

Claude Enterprise organizations: create a scoped admin key with only the
`read:members` scope. Cartography needs nothing more, and the key cannot change
anything. Enterprise organizations have no workspaces or API keys, so
Cartography syncs the organization and its users and skips the rest.

Store the key in an environment variable and pass its name:

```bash
cartography \
  --selected-modules anthropic \
  --anthropic-apikey-env-var ANTHROPIC_API_KEY
```

## Option 2: Workload identity federation

With [workload identity federation](https://platform.claude.com/docs/en/manage-claude/workload-identity-federation),
Cartography stores no Anthropic credential. It exchanges an OIDC token from the
environment it runs in (a Kubernetes service account, AWS, GitHub Actions, and
so on) for an access token that expires on its own.

1. In the Claude Console, open **Settings > Workload identity** and register
   the OIDC issuer that signs Cartography's identity token.
1. Create a service account with the `admin` organization role.
1. Create a federation rule that matches Cartography's token subject and the
   audience `https://api.anthropic.com`, targets that service account, and has
   the `org:admin` scope. The Admin API accepts no narrower scope.
1. Run Cartography with the path to its identity token and the IDs from the
   Console:

```bash
cartography \
  --selected-modules anthropic \
  --anthropic-identity-token-file /var/run/secrets/anthropic.com/token \
  --anthropic-federation-rule-id fdrl_... \
  --anthropic-organization-id 00000000-0000-0000-0000-000000000000 \
  --anthropic-service-account-id svac_...
```

Add `--anthropic-workspace-id` when the federation rule covers several
workspaces.

Cartography reads the token file every time it exchanges it, so a token that
your platform rotates in place, such as a projected Kubernetes service account
token, keeps working across a long sync.

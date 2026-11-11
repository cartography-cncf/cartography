# Anthropic Configuration

Cartography authenticates to the Anthropic Admin API with an Admin API key or
with workload identity federation. Choose one.

## Option 1: Admin API key

The kind of key depends on your organization:

- **Claude Console**: Create an Admin API key in the
  [Claude Console](https://platform.claude.com/settings/admin-keys). Console
  admin keys have full Admin API access.
- **Claude Enterprise**: Create a scoped admin key with only the
  `read:members` scope. Cartography needs nothing more, and the key can't change
  anything. Enterprise organizations have no workspaces or API keys, so
  Cartography syncs the organization and its users and skips the rest.

Store the key in an environment variable, and pass the variable's name to
Cartography:

```bash
cartography \
  --selected-modules anthropic \
  --anthropic-apikey-env-var ANTHROPIC_API_KEY
```

## Option 2: Workload identity federation

With [workload identity federation](https://platform.claude.com/docs/en/manage-claude/workload-identity-federation),
Cartography stores no Anthropic credential. It exchanges an OIDC token from the
environment that it runs in for an access token that expires on its own. For
example, the OIDC token can come from a Kubernetes service account, AWS, or
GitHub Actions.

1. In the Claude Console, go to **Settings > Workload identity** and register
   the OIDC issuer that signs Cartography's identity token.
1. Create a service account with the `admin` organization role.
1. Create a federation rule with these settings:
   - **Subject**: the subject of Cartography's identity token
   - **Audience**: `https://api.anthropic.com`
   - **Service account**: the service account from the previous step
   - **Scope**: `org:admin`. The Admin API accepts no narrower scope.
1. Run Cartography with the path to its identity token and the IDs from the
   Claude Console:

   ```bash
   cartography \
     --selected-modules anthropic \
     --anthropic-identity-token-file /var/run/secrets/anthropic.com/token \
     --anthropic-federation-rule-id fdrl_... \
     --anthropic-organization-id 00000000-0000-0000-0000-000000000000 \
     --anthropic-service-account-id svac_...
   ```

   If the federation rule covers more than one workspace, also pass
   `--anthropic-workspace-id`.

Anthropic accepts each identity token only once, so Cartography exchanges a
token again only after the token file holds a new one. Give the federation rule
a token lifetime that's longer than a sync, or read the token from a file that
your platform rotates in place, such as a projected Kubernetes service account
token.

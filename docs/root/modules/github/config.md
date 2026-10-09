# GitHub Configuration

## Authentication

GitHub supports fine-grained personal access tokens (PATs), classic PATs, and
GitHub Apps. Fine-grained PATs provide the narrowest token permissions and can
be scoped to an organization.

### Fine-grained PAT

1. Open **GitHub Settings**, then **Developer settings**, **Personal access
   tokens**, and **Fine-grained tokens**.
2. Select **Generate new token**.
3. Give the token a name such as `cartography-ingest`.
4. Set an expiration that follows your security policy. A 90-day expiration is
   recommended.
5. Select your organization as the resource owner and select **All
   repositories** for repository access.
6. Apply the permissions listed below, generate the token, and copy it
   immediately.

When an organization owns the token, Cartography retrieves user emails and
profiles from organization membership data. No account-level permissions are
required.

### Classic PAT

Use a classic PAT when fine-grained PATs are unavailable, including some
GitHub Enterprise configurations, or when GHCR ingestion requires
`read:packages`.

1. Open **GitHub Settings**, then **Developer settings**, **Personal access
   tokens**, and **Tokens (classic)**.
2. Select **Generate new token**.
3. Apply the scopes listed below, generate the token, and copy it immediately.

### GitHub App

GitHub App authentication uses short-lived, installation-scoped tokens.

1. [Create a GitHub App](https://docs.github.com/en/apps/creating-github-apps)
   with the repository and organization permissions listed below.
2. Install the App on each target organization.
3. Record the **Client ID** and **Installation ID**. The installation ID is in
   the installation URL:
   `https://github.com/organizations/{org}/settings/installations/{installation_id}`.
4. Generate and download a private key from the App settings page.

## Required Permissions

Fine-grained PATs and GitHub Apps require these repository permissions:

| Permission | Access | Purpose |
|------------|--------|---------|
| **Administration** | Read | Collaborators and branch protection rules |
| **Contents** | Read | Repository files, commit history, and dependency manifests |
| **Metadata** | Read | Repository discovery and basic information |

They also require the organization **Members: Read** permission for members,
teams, team membership, user profiles, and email addresses.

For collaborator and branch protection coverage, the credential owner must
also be an organization owner or have administrator access on the repositories.
The **Administration: Read** token permission alone does not grant those
rights.

Classic PATs require these scopes:

| Scope | Purpose |
|-------|---------|
| `repo` | Repository access. Use `public_repo` for public repositories only. |
| `read:org` | Organization membership and team data |
| `read:user` | User profile information |
| `user:email` | User email addresses |

## Optional Permissions

Without these permissions, Cartography logs warnings and skips the unavailable
data while continuing ingestion.

| Data | Fine-grained PAT or GitHub App | Classic PAT |
|------|--------------------------------|-------------|
| Actions workflows, runs, and artifacts | Repository **Actions: Read** | Included in `repo` |
| Dependabot alerts | Repository **Dependabot alerts: Read** | `security_events` for private repositories; `public_repo` is sufficient for public repositories |
| Deployment environments | Repository **Environments: Read** | Included in `repo` |
| Repository secret metadata | Repository **Secrets: Read** | Included in `repo` |
| Repository variables | Repository **Variables: Read** | Included in `repo` |
| Organization secret metadata | Organization **Secrets: Read** | Included in `read:org` |
| Organization variables | Organization **Variables: Read** | Included in `read:org` |
| GHCR packages, image manifests, layers, tags, and SLSA attestations | GitHub App permissions; fine-grained PATs cannot access GitHub Packages | `read:packages` |
| Fine-grained PAT inventory | GitHub App with organization **Personal access tokens: Read**; PAT authentication is not supported | Not available |
| Classic PAT inventory | Not available | SAML SSO credential authorizations on SAML-enabled organizations, organization owner access, and `read:org` |
| Two-factor authentication status | Organization owner access | Organization owner access |
| Organization settings: base repository permission, repository creation and forking restrictions, 2FA requirement, and legacy security defaults for new repositories | Organization owner access | Organization owner access and `admin:org` |
| Verified and approved domains, IP allow list status, and email notification restriction | Organization owner access with organization **Administration: Read** | Organization owner access and `admin:org` |
| Actions policy: enabled repositories, allowed actions, SHA pinning, and default `GITHUB_TOKEN` permissions | Organization **Administration: Read** | `admin:org` |
| Copilot policy and seat count | Organization owner access with organization **GitHub Copilot Business: Read** or **Administration: Read** | Organization owner access and `manage_billing:copilot` or `read:org` |
| Repository secret scanning, push protection, Advanced Security, and Dependabot security updates status | Repository **Administration: Read**, with repository administrator, organization owner, or security manager access | `repo`, with repository administrator, organization owner, or security manager access |
| Installed GitHub Apps and their permissions | Organization owner access with organization **Administration: Read** | Organization owner access and `read:org` |
| Organization webhooks | Organization owner access with organization **Webhooks: Read** | Organization owner access and `admin:org_hook` |
| Repository webhooks | Repository **Webhooks: Read**, with repository administrator access | `read:repo_hook`, with repository administrator access |
| Enterprise owners | Appropriate GitHub Enterprise permissions | Appropriate GitHub Enterprise permissions |
| SAML external identities | GitHub App installation token with organization **Members: Read**; fine-grained PATs are not supported by this GraphQL field | Organization owner access and `read:org` or `admin:org` |

GitHub exposes secret metadata, such as names and timestamps, but never secret
values.

### Organization and repository security settings

GitHub only returns most organization settings to organization owners, and
repository `security_and_analysis` settings to repository administrators,
organization owners, and security managers. When GitHub does not return a
setting, Cartography leaves the property null, so null means unknown rather than
disabled. Each source is fetched independently: a missing permission for one,
such as Copilot, does not affect the others. Other request failures, such as
server errors or timeouts, stop the GitHub sync for that organization instead of
overwriting known settings with null. Domains are only removed from the
graph after a complete domain list is fetched.

GitHub has deprecated the organization `*_enabled_for_new_repositories` security
defaults in favor of code security configurations, so they may be null even for
owners. Use the repository-level `secret_scanning_enabled` and
`secret_scanning_push_protection_enabled` properties for current coverage.

GitHub does not have an organization default repository visibility setting.
Repository creation is restricted by visibility through the
`members_can_create_public_repositories`,
`members_can_create_private_repositories`, and
`members_can_create_internal_repositories` properties.

### GitHub Apps and webhooks

Each installed GitHub App becomes a `GitHubAppInstallation` node, which also has
the `ThirdPartyApp` ontology label. Its `write_permissions` list names the
permissions granted with write or admin access, and `permissions`
keeps the full grant as JSON. GitHub does not list which repositories an
installation with `repository_selection: selected` can access to organization
owners, so those repository links are not ingested.

Organization and repository webhooks become `GitHubWebhook` nodes. Webhook
target URLs often embed credentials, so Cartography stores only the target
scheme and host, along with TLS verification and whether a secret is configured.
Repository webhooks also record their latest delivery status. GitHub never
returns webhook secret values. Stale webhooks are only removed after the
organization list and every repository list were fetched: a repository the
credential cannot administer, or any other denied listing, preserves previously
synced webhooks. Other request failures stop the GitHub sync for that
organization.

### SAML identity mapping

Cartography reads the organization's
[SAML identity provider](https://docs.github.com/en/graphql/reference/objects#organizationidentityprovider)
and paginates its external identities. Each `GitHubExternalIdentity` belongs to a
`GitHubOrganization` through `RESOURCE`; a linked `GitHubUser` points to it through
`HAS_IDENTITY`. The SAML NameID is stored separately from public profile and
verified-domain email addresses because it may be an opaque identifier.

After GitHub and your identity provider have synced, the ontology module can
link organization members to existing canonical `User` nodes using email-shaped
NameIDs. Matching ignores surrounding whitespace and letter case, requires a
single canonical user across the account's organization identities, and skips
accounts whose public or organization verified-domain emails identify a different
canonical user, even when no email-based account link exists. A personal email
or alias without a competing canonical owner does not contradict the SAML link. These
emails are normalized during ingestion into `GitHubUser.normalized_emails`;
raw email properties are preserved. Existing GitHub users need a GitHub resync
before SAML linking uses this conflict check. The GitHub and ontology syncs use
the same Python normalization for
`GitHubExternalIdentity.saml_name_id_normalized` and the indexed
`User.normalized_email`, including Unicode whitespace. The join compares these
stored values, preserving the raw NameID, primary email, and canonical user ID. For
example, configure `--ontology-users-source okta` to use Okta as the source of
canonical users. SAML ingestion does not create canonical users on its own.

Unavailable providers and denied access preserve prior identity data. A complete
empty identity list removes stale identities for that organization. Transient
transport failures, GraphQL timeouts, and rate limits retry the same page up to
five attempts. Each attempt checks the GraphQL budget on the configured GitHub
instance and waits for its reset when necessary. HTTP rate-limit delays honor
GitHub's retry/reset headers, including resets more than five minutes away.
Secondary limits without a reset start with a one-minute wait and back off
exponentially. Unrecovered API errors log a warning and skip identity writes and
cleanup, allowing other GitHub resources and organizations to sync. Graph write
and cleanup errors still propagate. Refreshing the
ontology removes links that no longer have an identity basis; SAML and existing
GitHub email linking share the same relationship cleanup.

## Configure Cartography

Cartography accepts GitHub credentials as base64-encoded JSON. The configuration
supports multiple organizations and GitHub instances.

For PAT authentication:

```python
import base64
import json

config = {
    "organization": [
        {
            "token": "ghp_your_token_here",
            "url": "https://api.github.com/graphql",
            "name": "your-org-name",
        },
        # Optional additional organization or GitHub Enterprise instance:
        # {
        #     "token": "ghp_enterprise_token",
        #     "url": "https://github.example.com/api/graphql",
        #     "name": "enterprise-org-name",
        # },
    ]
}

encoded = base64.b64encode(json.dumps(config).encode()).decode()
print(encoded)
```

For GitHub App authentication:

```python
config = {
    "organization": [
        {
            "client_id": "Iv1.abc123def456",
            "private_key": open("your-app.private-key.pem").read(),
            "installation_id": "12345678",
            "url": "https://api.github.com/graphql",
            "name": "your-org-name",
        },
    ]
}
```

You can mix PAT and App authentication across organizations in the same
configuration. Base64-encode the final configuration and set it in an
environment variable:

```bash
export GITHUB_CONFIG="eyJvcmdhbml6YXRpb24iOi..."
```

## Run Cartography

```bash
cartography \
  --selected-modules github \
  --github-config-env-var GITHUB_CONFIG
```

## Advanced Configuration

| CLI flag | Description |
|----------|-------------|
| `--github-config-env-var` | Environment variable containing the base64-encoded configuration |
| `--github-commit-lookback-days` | Number of days of commit history to ingest. The default is 30. |

For GitHub Enterprise, use the same token scopes and permissions. Set `url` to
the enterprise GraphQL endpoint:

```python
{
    "token": "your_enterprise_token",
    "url": "https://github.your-company.com/api/graphql",
    "name": "your-enterprise-org",
}
```

## Security rules

These experimental rules check the GitHub security posture ingested above. Run
them against the graph with `cartography-rules run <rule>`:

| Rule | Checks | Data it needs |
|------|--------|---------------|
| `github_secret_scanning_disabled` | Unarchived repositories without secret scanning or push protection | Repository security settings |
| `github_organization_security_settings` | 2FA not required, write or admin base permission, members can create public repositories, notifications not restricted to verified domains | Organization settings |
| `github_actions_permissive_policy` | With Actions enabled: any action allowed, a write `GITHUB_TOKEN` by default, workflows that can approve pull requests | Actions policy |
| `github_app_sensitive_permissions` | Active GitHub Apps with write access to code, workflows, secrets, webhooks, runners, members, or administration | Installed GitHub Apps |
| `github_webhook_insecure_delivery` | Active webhooks without a signing secret, without TLS certificate verification, or over plain HTTP | Organization and repository webhooks |

Unknown values are skipped, so a check that evaluated no assets had nothing to
test, which does not mean the organization is secure. Grant the matching
optional permissions above for full coverage. See
[Running Rules](../../usage/rules.md) for connection options.

## Troubleshooting

| Issue | Solution |
|-------|----------|
| `FORBIDDEN` warnings for collaborators or branch protection rules | Ensure a fine-grained PAT includes repository **Administration: Read** and the token owner has organization owner or repository administrator rights. |
| `403 Forbidden` for `/orgs/{org}/packages` and no `GitHubPackage` nodes | GHCR ingestion requires `read:packages` on a classic PAT or a GitHub App. Fine-grained PATs cannot access GitHub Packages. |
| No `GitHubPersonalAccessToken` nodes | Fine-grained PAT inventory requires GitHub App authentication with **Personal access tokens: Read**. Classic PAT metadata is limited to SAML SSO credential authorizations on SAML-enabled organizations. |
| Empty dependency data | Ensure the [dependency graph](https://docs.github.com/en/code-security/supply-chain-security/understanding-your-software-supply-chain/about-the-dependency-graph) is enabled. |
| Missing two-factor authentication status | This status is visible only to organization owners. |
| Null organization settings, such as `default_repository_permission` or `actions_allowed_actions` | These settings are visible only to organization owners. Classic PATs also need `admin:org`. |
| Null `secret_scanning_enabled` on repositories | GitHub only reports security settings to repository administrators, organization owners, and security managers. |
| No `GitHubAppInstallation` or `GitHubWebhook` nodes | These require organization owner access and the permissions listed under Optional Permissions. Repository webhooks also require administrator access on each repository. |
| Rate limiting | Cartography sleeps until the quota resets. |

## References

- [Managing GitHub personal access tokens](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/managing-your-personal-access-tokens)
- [Fine-grained PAT limitations](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/managing-your-personal-access-tokens#fine-grained-personal-access-tokens-limitations)
- [Creating a GitHub App](https://docs.github.com/en/apps/creating-github-apps)
- [GitHub dependency graph](https://docs.github.com/en/code-security/supply-chain-security/understanding-your-software-supply-chain/about-the-dependency-graph)

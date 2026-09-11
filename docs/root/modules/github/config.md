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
| Enterprise owners | Appropriate GitHub Enterprise permissions | Appropriate GitHub Enterprise permissions |
| SAML external identities | GitHub App installation token with organization **Members: Read**; fine-grained PATs are not supported by this GraphQL field | Organization owner access and `read:org` or `admin:org` |

GitHub exposes secret metadata, such as names and timestamps, but never secret
values.

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
conflicts with GitHub public or organization verified-domain email links. The
ontology sync populates an indexed `User.normalized_email` for this match while
preserving the original primary email and canonical user ID. For
example, configure `--ontology-users-source okta` to use Okta as the source of
canonical users. SAML ingestion does not create canonical users on its own.

Unavailable providers and denied access preserve prior identity data. A complete
empty identity list removes stale identities for that organization. Transient
transport failures, GraphQL timeouts, and rate limits retry the same page up to
five attempts. HTTP rate-limit delays honor GitHub's retry/reset headers; a wait
longer than five minutes fails the snapshot instead of retrying early. GraphQL
rate-limit errors wait one minute between attempts. Unrecovered API errors fail
the snapshot before any identity writes or cleanup. Refreshing the
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

## Troubleshooting

| Issue | Solution |
|-------|----------|
| `FORBIDDEN` warnings for collaborators or branch protection rules | Ensure a fine-grained PAT includes repository **Administration: Read** and the token owner has organization owner or repository administrator rights. |
| `403 Forbidden` for `/orgs/{org}/packages` and no `GitHubPackage` nodes | GHCR ingestion requires `read:packages` on a classic PAT or a GitHub App. Fine-grained PATs cannot access GitHub Packages. |
| No `GitHubPersonalAccessToken` nodes | Fine-grained PAT inventory requires GitHub App authentication with **Personal access tokens: Read**. Classic PAT metadata is limited to SAML SSO credential authorizations on SAML-enabled organizations. |
| Empty dependency data | Ensure the [dependency graph](https://docs.github.com/en/code-security/supply-chain-security/understanding-your-software-supply-chain/about-the-dependency-graph) is enabled. |
| Missing two-factor authentication status | This status is visible only to organization owners. |
| Rate limiting | Cartography sleeps until the quota resets. |

## References

- [Managing GitHub personal access tokens](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/managing-your-personal-access-tokens)
- [Fine-grained PAT limitations](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/managing-your-personal-access-tokens#fine-grained-personal-access-tokens-limitations)
- [Creating a GitHub App](https://docs.github.com/en/apps/creating-github-apps)
- [GitHub dependency graph](https://docs.github.com/en/code-security/supply-chain-security/understanding-your-software-supply-chain/about-the-dependency-graph)

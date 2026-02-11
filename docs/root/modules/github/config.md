## GitHub Configuration

Follow these steps to analyze GitHub repos and other objects with Cartography.

### Step 1: Create a Personal Access Token

GitHub supports two types of Personal Access Tokens (PATs). **We recommend using Fine-grained PATs** as they provide more granular control and can be scoped to specific organizations.

#### Option A: Fine-grained PAT (Recommended)

Fine-grained PATs offer better security through minimal permissions and organization-level scoping.

1. Go to **GitHub → Settings → Developer settings → Personal access tokens → Fine-grained tokens**
2. Click **Generate new token**
3. Configure the token:

   | Setting | Value |
   |---------|-------|
   | **Token name** | `cartography-ingest` (or your preference) |
   | **Expiration** | Per your security policy (90 days recommended) |
   | **Resource owner** | Select your **organization** (recommended) |
   | **Repository access** | **All repositories** |

4. Set the following permissions:

   **Repository permissions:**

   | Permission | Access | Required | Why |
   |------------|--------|----------|-----|
   | **Actions** | Read | Optional | GitHub Actions workflows, runs, and artifacts. |
   | **Administration** | Read | Yes (for collaborator/branch protection coverage) | Collaborators and branch protection rules. Without this, Cartography logs warnings and skips this data. |
   | **Contents** | Read | Yes | Repository files, commit history, dependency manifests. |
   | **Environments** | Read | Optional | Deployment environments configuration. |
   | **Metadata** | Read | Yes | Auto-added. Repository discovery and basic info. |
   | **Secrets** | Read | Optional | Repository secrets metadata (names, creation dates). |
   | **Variables** | Read | Optional | Repository variables for Actions workflows. |

   **Organization permissions:**

   | Permission | Access | Required | Why |
   |------------|--------|----------|-----|
   | **Members** | Read | Yes | Organization members, teams, team membership, user profiles/emails. |
   | **Secrets** | Read | Optional | Organization secrets metadata (names, creation dates). |
   | **Variables** | Read | Optional | Organization variables for Actions workflows. |

   > **Note:** The Secrets permission only provides access to secret **metadata** (name, creation date, update date). GitHub never exposes the actual secret values through its API—they are encrypted and cannot be retrieved.

5. Click **Generate token** and copy it immediately.

> **Note:** When the token's resource owner is an organization, user emails and profiles are retrieved from organization membership data. No account-level permissions are required.

> **Note:** For collaborator and branch protection data, the token owner must also be an **Organization Owner** or have **Admin access** on repositories. The `Administration: Read` permission alone is not sufficient—the user must already have these rights.

#### Option B: Classic PAT

Classic PATs use broader OAuth scopes. Use this option if fine-grained PATs are not available (e.g., some GitHub Enterprise configurations).

1. Go to **GitHub → Settings → Developer settings → Personal access tokens → Tokens (classic)**
2. Click **Generate new token**
3. Select the following scopes:

   | Scope | Why |
   |-------|-----|
   | `repo` | Repository access (use `public_repo` for public repos only) |
   | `read:org` | Organization membership and team data |
   | `read:user` | User profile information |
   | `user:email` | User email addresses |

4. Click **Generate token** and copy it immediately.

### Optional: Additional Permissions for Full Data Access

Some data requires elevated permissions. Without these, Cartography will log warnings and continue ingestion, skipping the unavailable data.

| Data | Requirement |
|------|-------------|
| **Collaborators** | For fine-grained PATs, both are required: `Repository -> Administration: Read` on the token and token-owner rights as an **Organization Owner** or **Admin** on the repositories. |
| **Branch protection rules** | Same as collaborators: both `Repository -> Administration: Read` and owner/admin-equivalent rights are required. |
| **Two-factor authentication status** | Visible only to Organization Owners. |
| **Enterprise owners** | Requires GitHub Enterprise with appropriate enterprise-level permissions. |

### Alternative: GitHub App Authentication

GitHub App authentication provides better security through short-lived tokens and granular, installation-scoped permissions. Use this instead of PATs when you need app-level (not user-level) access.

1. [Create a GitHub App](https://docs.github.com/en/apps/creating-github-apps) with the same repository and organization permissions listed above.
2. Install the App on your target organization(s).
3. Note the **Client ID** (from the App's settings page) and the **Installation ID** (from the URL when viewing the installation: `https://github.com/organizations/{org}/settings/installations/{installation_id}`).
4. Generate and download a **private key** from the App's settings page.

Then configure Cartography with the App credentials instead of a PAT (see Step 2 below).

### Step 2: Configure Cartography

Cartography accepts GitHub credentials as a base64-encoded JSON configuration. This format supports multiple GitHub instances (e.g., public GitHub and GitHub Enterprise).

1. Create your configuration object:

    ```python
    import json
    import base64

    config = {
        "organization": [
            {
                "token": "ghp_your_token_here",
                "url": "https://api.github.com/graphql",
                "name": "your-org-name",
            },
            # Optional: Add additional orgs or GitHub Enterprise instances
            # {
            #     "token": "ghp_enterprise_token",
            #     "url": "https://github.example.com/api/graphql",
            #     "name": "enterprise-org-name",
            # },
        ]
    }

    # Encode the configuration
    encoded = base64.b64encode(json.dumps(config).encode()).decode()
    print(encoded)
    ```

For **GitHub App authentication**, use this format instead:

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

You can mix PAT and App authentication across organizations in the same config.

2. Set the encoded value as an environment variable:

    ```bash
    export GITHUB_CONFIG="eyJvcmdhbml6YXRpb24iOi..."
    ```

3. Run Cartography with the GitHub module:

    ```bash
    cartography --github-config-env-var GITHUB_CONFIG
    ```

### Configuration Options

| CLI Flag | Description |
|----------|-------------|
| `--github-config-env-var` | Environment variable containing the base64-encoded config |
| `--github-commit-lookback-days` | Number of days of commit history to ingest (default: 30) |

### GitHub Enterprise

For GitHub Enterprise, use the same token scopes/permissions as above. Set the `url` field in your configuration to your enterprise GraphQL endpoint:

```python
{
    "token": "your_enterprise_token",
    "url": "https://github.your-company.com/api/graphql",
    "name": "your-enterprise-org",
}
```

### Troubleshooting

| Issue | Solution |
|-------|----------|
| `FORBIDDEN` warnings for collaborators/branch protection rules | Ensure fine-grained PAT includes `Repository -> Administration: Read` and the token owner has Organization Owner or repository Admin rights; otherwise Cartography will skip this enrichment and continue. |
| Empty dependency data | Ensure the [dependency graph](https://docs.github.com/en/code-security/supply-chain-security/understanding-your-software-supply-chain/about-the-dependency-graph) is enabled on your repositories. |
| Missing 2FA status | Only visible to Organization Owners. |
| Rate limiting | Cartography handles rate limits automatically by sleeping until the quota resets. |

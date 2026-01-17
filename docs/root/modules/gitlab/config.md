## GitLab Configuration

Follow these steps to configure Cartography to sync GitLab organization, group, project, and related data.

### Prerequisites

1. A GitLab instance (self-hosted or gitlab.com)
2. A GitLab personal access token with the required scopes (see below)
3. The numeric ID of the GitLab organization (top-level group) to sync

### Creating a GitLab Personal Access Token

1. Navigate to your GitLab instance (e.g., `https://gitlab.com` or `https://gitlab.example.com`)
2. Go to **User Settings** → **Access Tokens** (or directly to `https://your-gitlab-instance/-/profile/personal_access_tokens`)
3. Click **Add new token**
4. Configure your token:
   - **Token name**: `cartography-sync`
   - **Scopes**: Select `read_user`, `read_repository`, and `read_api`
   - **Expiration date**: Set according to your security policy
5. Click **Create personal access token**
6. **Important**: Copy the token immediately - you won't be able to see it again

### Required Token Permissions

The token requires the following scopes:

| Scope | Purpose |
|-------|---------|
| `read_user` | Access user profile information for group/project membership |
| `read_repository` | Access repository metadata, branches, and file contents |
| `read_api` | Access groups, projects, dependencies, and language statistics |

These scopes provide read-only access to:
- Organizations (top-level groups) and nested groups
- Projects and their metadata
- Branches and default branch information
- Dependency files (package.json, requirements.txt, etc.)
- Dependencies extracted from dependency files
- Project language statistics

### Finding Your Organization ID

The organization ID is the numeric ID of the top-level GitLab group you want to sync. To find it:

1. Navigate to your group's page on GitLab (e.g., `https://gitlab.com/your-organization`)
2. The group ID is displayed below the group name, or you can find it via the API:
   ```bash
   curl -H "PRIVATE-TOKEN: your-token" "https://gitlab.com/api/v4/groups/your-organization"
   ```
   The `id` field in the response is your organization ID.

### Configuration

1. Set your GitLab token in an environment variable:
   ```bash
   export GITLAB_TOKEN="glpat-your-token-here"
   ```

2. Run Cartography with GitLab module:
   ```bash
   cartography \
     --neo4j-uri bolt://localhost:7687 \
     --selected-modules gitlab \
     --gitlab-organization-id 12345678 \
     --gitlab-token-env-var "GITLAB_TOKEN"
   ```

### Configuration Options

| Parameter | CLI Argument | Environment Variable | Required | Default | Description |
|-----------|-------------|---------------------|----------|---------|-------------|
| GitLab URL | `--gitlab-url` | N/A | No | `https://gitlab.com` | The GitLab instance URL. Only set for self-hosted instances. |
| GitLab Token | `--gitlab-token-env-var` | Set by you | Yes | N/A | Name of the environment variable containing your GitLab personal access token |
| Organization ID | `--gitlab-organization-id` | N/A | Yes | N/A | The numeric ID of the top-level GitLab group (organization) to sync |

### Performance Considerations

- **Language detection**: Fetches programming language statistics for all projects using parallel async requests (10 concurrent by default). Languages are stored as a JSON property on each project.
- **Large instances**: For ~3000 projects, language fetching takes approximately 5-7 minutes
- **API rate limits**: GitLab.com has rate limits (2000 requests/minute for authenticated users). Self-hosted instances may have different limits

### Multi-Instance Support

Cartography supports syncing from multiple GitLab instances simultaneously. Repository and group IDs are prefixed with the GitLab instance URL to prevent collisions:

```
https://gitlab.com/projects/12345
https://gitlab.example.com/projects/12345
```

Both can exist in the same Neo4j database without conflicts.

### Example: Self-Hosted GitLab

```bash
export GITLAB_TOKEN="glpat-abc123xyz"

cartography \
  --neo4j-uri bolt://localhost:7687 \
  --selected-modules gitlab \
  --gitlab-url "https://gitlab.example.com" \
  --gitlab-organization-id 12345678 \
  --gitlab-token-env-var "GITLAB_TOKEN"
```

### Troubleshooting

**Connection timeout:**
- Default timeout is 60 seconds
- For slow GitLab instances, the sync may take longer during language detection
- Check GitLab instance health if repeated timeouts occur

**Missing language data:**
- Some projects may not have language statistics available (empty repos, binary-only repos)
- Errors fetching languages for individual projects are logged as warnings but don't stop the sync

**Missing dependency data:**
- Dependency scanning requires projects to have supported manifest files (package.json, requirements.txt, etc.)
- The GitLab Dependency Scanning feature must be enabled for the project

**Permission errors:**
- Ensure your token has all required scopes: `read_user`, `read_repository`, `read_api`
- Verify the token hasn't expired
- Check that the GitLab user has access to the organization and projects you want to sync

**Organization not found:**
- Verify the `--gitlab-organization-id` is the correct numeric ID (not the group path)
- Ensure the token's user has access to the organization

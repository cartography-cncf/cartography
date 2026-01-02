## GitLab Configuration

Follow these steps to configure Cartography to sync GitLab repository and group data.

### Prerequisites

1. A GitLab instance (self-hosted or gitlab.com)
2. A GitLab personal access token with `read_api` or `api` scope

### Creating a GitLab Personal Access Token

1. Navigate to your GitLab instance (e.g., `https://gitlab.com` or `https://gitlab.example.com`)
2. Go to **User Settings** → **Access Tokens** (or directly to `https://your-gitlab-instance/-/profile/personal_access_tokens`)
3. Click **Add new token**
4. Configure your token:
   - **Token name**: `cartography-sync`
   - **Scopes**: Select `read_api` (recommended) or `api` (if read_api is not available)
   - **Expiration date**: Set according to your security policy
5. Click **Create personal access token**
6. **Important**: Copy the token immediately - you won't be able to see it again

### Required Token Permissions

The token needs `read_api` scope to access:
- Projects (repositories) list and metadata
- Group (namespace) information
- Project language statistics

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
     --gitlab-url "https://gitlab.com" \
     --gitlab-token-env-var "GITLAB_TOKEN"
   ```

### Configuration Options

| Parameter | CLI Argument | Environment Variable | Required | Description |
|-----------|-------------|---------------------|----------|-------------|
| GitLab URL | `--gitlab-url` | N/A | Yes | The GitLab instance URL (e.g., `https://gitlab.com` or `https://gitlab.example.com`) |
| GitLab Token | `--gitlab-token-env-var` | Set by you | Yes | Name of the environment variable containing your GitLab personal access token |

### Performance Considerations

- **Language detection**: Fetches programming language statistics for ALL repositories using parallel execution (10 workers by default)
- **Large instances**: For ~3000 repositories, language fetching takes approximately 5-7 minutes
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
  --gitlab-token-env-var "GITLAB_TOKEN"
```

### Troubleshooting

**Connection timeout:**
- Default timeout is 60 seconds
- For slow GitLab instances, the sync may take longer during language detection
- Check GitLab instance health if repeated timeouts occur

**Missing language data:**
- Some repositories may not have language statistics available (empty repos, binary-only repos)
- Errors fetching languages for individual repos are logged as warnings but don't stop the sync

**Permission errors:**
- Ensure your token has `read_api` scope
- Verify the token hasn't expired
- Check that the GitLab user has access to the projects you want to sync

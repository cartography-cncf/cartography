## GitLab

Cartography can sync repository, group, and programming language data from GitLab instances.

### Module Features

- **Repositories**: Comprehensive metadata for all GitLab projects including URLs, statistics, feature flags, and access settings
- **Groups**: GitLab group (namespace) information with ownership relationships
- **Programming Languages**: Language detection with usage percentages for all repositories
- **Multi-instance support**: Sync from multiple GitLab instances without ID conflicts
- **Performance optimized**: Parallel language fetching for large instances (tested with 3000+ repos)

### Data Collected

#### GitLabRepository Nodes
- Repository identification and paths
- Multiple URL formats (web, HTTP clone, SSH clone, README)
- Visibility and access settings (private/internal/public, archived)
- Statistics (stars, forks, open issues)
- Feature flags (issues, merge requests, wiki, snippets, container registry)
- Timestamps (created, last activity)
- Default branch information

#### GitLabGroup Nodes
- Group names and paths
- Full namespace hierarchy
- Visibility settings
- Web URLs

#### Programming Language Analysis
- Language detection for all repositories
- Usage percentages (e.g., 65.5% Python, 34.5% JavaScript)
- Shared `ProgrammingLanguage` nodes across GitHub and GitLab modules

### Graph Relationships

```
(:GitLabGroup)-[:OWNER]->(:GitLabRepository)-[:LANGUAGE{percentage}]->(:ProgrammingLanguage)
```

### Configuration

See [GitLab Configuration](config.md) for setup instructions.

### Schema

See [GitLab Schema](schema.md) for detailed schema documentation and sample queries.

### Scalability

The GitLab module has been tested with large instances and uses parallel execution (10 concurrent workers) to efficiently handle language detection across thousands of repositories.

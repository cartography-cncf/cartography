# GitLab

The GitLab module ingests a configured top-level group as an organization,
including nested groups, projects, current members, branches, dependency
scanning results, CI/CD variables and pipeline configuration, deployment
environments, runners, and container registry data.

Only current organization and group members are represented as `GitLabUser`
nodes. Commit activity links those users to projects by email when available,
with a display-name fallback for current members. Former members and external
contributors who are not current members are not ingested.

CI/CD variable values are intentionally not stored. The graph contains only
their metadata, including the `protected`, `masked`, `masked_and_hidden`, and
`environment_scope` security signals. Environment-to-variable relationships
currently support an exact environment-name match and the `*` wildcard. GitLab
glob scopes such as `production/*` are not expanded by Cartography.

Container images are keyed by digest and layers by their uncompressed
`diff_id`, which supports cross-registry layer deduplication. Provenance
attestations and Dockerfile command analysis can link ontology `Image` nodes to
the GitLab projects that packaged them.

## Multi-instance behavior

Cartography can sync multiple GitLab instances. Repository and group IDs are
prefixed with the GitLab instance URL, so the same numeric ID from gitlab.com
and a self-hosted instance can coexist in Neo4j.

Language statistics are fetched for all projects with 10 concurrent requests
by default and stored as JSON on each project. As a reference point, fetching
languages for approximately 3000 projects can take 5-7 minutes. GitLab.com
limits authenticated clients to 2000 requests per minute; self-hosted limits
may differ.

See [configuration](config.md) for access requirements and setup,
[example queries](queries.md) for common investigations, and the generated
[schema](schema.md) for fields and relationships.

```{toctree}
config
queries
schema
```

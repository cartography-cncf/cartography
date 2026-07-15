# GitHub

The GitHub module ingests organizations, users, teams, repositories, repository
controls, Actions configuration, dependency data, Dependabot alerts, and GitHub
Container Registry (GHCR) metadata. See [configuration](config.md) for
authentication and required permissions, and the generated [schema](schema.md)
for node fields and relationships.

## Inventory limitations

Personal access token (PAT) inventory depends on APIs that GitHub exposes only
in specific contexts. Fine-grained PAT inventory requires GitHub App
authentication and the organization `Personal access tokens: Read` permission.
Classic PAT metadata is available only through SAML SSO credential
authorizations for SAML-enabled organizations. Cartography stores token metadata
only. It never stores token values, prefixes, or token fragments.

Repository ruleset bypass actors are intentionally unavailable. GitHub returns
them only to callers with write access to the ruleset, while Cartography is
designed to use read-only credentials.

GitHub exposes Actions secret metadata but never secret values. Actions variable
values, by contrast, are returned by the API and stored in plaintext in the
graph.

Collaborator relationships encode both affiliation and effective permission:
`DIRECT_COLLAB_*` and `OUTSIDE_COLLAB_*`, where the suffix is `ADMIN`,
`MAINTAIN`, `READ`, `TRIAGE`, or `WRITE`. Enterprise owners can control an
enterprise without appearing in an organization's member list. Such users use
the `UNAFFILIATED` relationship when Cartography can retrieve them.

## Dependency behavior

When GitHub's dependency graph provides only a version range, Cartography can
recover an exact version from a co-located `uv.lock` or `package-lock.json`.
It never applies a repository-root lockfile to a manifest in another directory.
Conflicting exact versions for the same shared dependency identifier are left
unresolved to avoid projecting an incorrect canonical `Package`.

Dependency and `PythonLibrary` nodes are shared globally across repositories and
organizations. Their cleanup therefore runs once after all configured GitHub
organizations have synced. Dependabot package, GHSA, CWE, and reference
identifiers remain properties. Cartography does not create package or CVE
relationships from those identifiers until identity can be normalized safely.

## GHCR behavior

GHCR images are keyed by digest. Layers are keyed by uncompressed `diff_id`,
which enables deduplication even when registries use different compressed
digests. SLSA provenance and Dockerfile analysis can link ontology `Image` nodes
to the GitHub repositories and workflows that produced them. Workloads from
other providers match GitHub container images by digest when their declarative
schemas expose compatible matcher fields.

## Compatibility model

The legacy `DependencyGraphManifest` label remains alongside
`GitHubDependencyGraphManifest` until v1.0.0. Deprecated compatibility edges
also remain beside their canonical ontology replacements: `GitHubUser-[:OWNS]->`
`GitHubPersonalAccessToken`, `GitHubTeam-[:MEMBER]->GitHubUser`, and
`GitHubTeam-[:MEMBER_OF_TEAM]->GitHubTeam`. New queries should prefer
`OWNED_BY` and the canonical `MEMBER_OF` edges.

```{toctree}
config
schema
```

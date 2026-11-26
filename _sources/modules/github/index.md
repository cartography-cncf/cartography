# GitHub

The GitHub module ingests organizations, users, teams, repositories, repository
controls, Actions configuration, dependency data, Dependabot alerts, GitHub
Container Registry (GHCR) metadata, and organization security posture: security
settings, verified domains, Actions and Copilot policies, repository secret
scanning status, installed GitHub Apps, and webhooks. See [configuration](config.md) for
authentication and required permissions, and the generated [schema](schema.md)
for node fields and relationships.

## Inventory limitations

Personal access token (PAT) inventory depends on APIs that GitHub exposes only
in specific contexts. Fine-grained PAT inventory requires GitHub App
authentication and the organization `Personal access tokens: Read` permission.
Classic PAT metadata is available only through SAML SSO credential
authorizations for SAML-enabled organizations, readable by a GitHub App with
organization `Administration: Read` or by a classic PAT of an organization owner
with `read:org`. Cartography stores token metadata
only. It never stores token values, prefixes, or token fragments.
A classic PAT is identified by GitHub's `authorized_credential_id`, the token's
own ID, so a token authorized for several organizations is one node with an
`AUTHORIZED_CREDENTIAL` edge from each organization. Each edge carries that
organization's `credential_id` (the SAML authorization to revoke),
`credential_authorized_at` and `credential_accessed_at`. An organization's sync
removes only its own edge, and the token node is deleted by the unscoped
cleanup that runs after all organizations have synced, once no organization
authorizes it. When GitHub omits `authorized_credential_id`, Cartography falls
back to the organization-scoped credential authorization ID, so that token is not
deduplicated across organizations. Fine-grained PATs have a single resource owner
and keep their `RESOURCE` edge.
When GitHub returns authorization or availability errors for either inventory
endpoint, Cartography skips cleanup so previously synced token metadata is
preserved.

Repository ruleset bypass actors are intentionally unavailable. GitHub returns
them only to callers with write access to the ruleset, while Cartography is
designed to use read-only credentials.

Which branch protection rule and which rulesets govern a repository's default
branch comes from GitHub rather than from matching patterns in Cartography: the
GraphQL `defaultBranchRef.branchProtectionRule` field and the REST
`GET /repos/{owner}/{repo}/rules/branches/{branch}` endpoint, called once per
repository that has a default branch and at least one ruleset. They are stored as
`GitHubBranchProtectionRule.protects_default_branch` and the
`applies_to_default_branch` property of `HAS_RULESET`.

When a credential cannot read a repository's branch protection rules or
rulesets, `branch_protection_rules_visible` or `rulesets_visible` on
`GitHubRepository` is false, and the default-branch protection facts and
`codeowners_review_not_required` do not evaluate that repository;
`codeowners_missing` still does, since it only needs the CODEOWNERS read. A truncated branch protection rule list also counts as not visible.
If the privileged fetch fails for the whole organization, branch protection rule
and ruleset cleanup is skipped so previously synced data is kept. Otherwise
cleanup runs, so a rule removed from a readable repository is not kept alive by
another repository that is unreadable.
`codeowners_readable` records whether every CODEOWNERS location on the default
branch could be read.

GitHub exposes Actions secret metadata but never secret values. Actions variable
values, by contrast, are returned by the API and stored in plaintext in the
graph.

Collaborator relationships encode both affiliation and effective permission:
`DIRECT_COLLAB_*` and `OUTSIDE_COLLAB_*`, where the suffix is `ADMIN`,
`MAINTAIN`, `READ`, `TRIAGE`, or `WRITE`. Enterprise owners can control an
enterprise without appearing in an organization's member list. Such users use
the `UNAFFILIATED` relationship when Cartography can retrieve them.

GitHub scopes a user's two-factor authentication status, enterprise ownership,
and verified-domain emails to the organization being synced. Cartography stores
each organization's values on the user's `MEMBER_OF` or `UNAFFILIATED`
relationship and combines them on the `GitHubUser` node, so a user in several
organizations keeps what any one of them reports. GitHub returns the two-factor
status only to organization owners: `has_2fa_enabled` is true when any
organization reports it enabled, false when none does and one reports it
disabled, and unset otherwise. A user with no `MEMBER_OF` or `UNAFFILIATED`
relationship to a synced organization, such as a repository collaborator, has
none of these properties.

## Dependency behavior

When GitHub's dependency graph provides only a version range, Cartography can
recover an exact version from a co-located `uv.lock` or `package-lock.json`.
It never applies a repository-root lockfile to a manifest in another directory.
Conflicting exact versions for the same shared dependency identifier are left
unresolved to avoid projecting an incorrect canonical `PackageVersion`.

Dependency and `PythonLibrary` nodes are shared globally across repositories and
organizations. Their cleanup therefore runs once after all configured GitHub
organizations have synced. Dependabot package, GHSA, CWE, and reference
identifiers remain properties. Cartography does not create package or CVE
relationships from those identifiers until identity can be normalized safely.

## GHCR behavior

GHCR images are keyed by digest. Layers are keyed by uncompressed `diff_id`,
which enables deduplication even when registries use different compressed
digests. SLSA provenance, the OCI `org.opencontainers.image.source` and
`org.opencontainers.image.revision` labels (or BuildKit's `vcs.source` and
`vcs.revision`), and Dockerfile analysis can link ontology `Image` nodes to
the GitHub repositories and workflows that produced them. When an attestation
names a repository, all of the image's source fields come from that attestation,
including any it leaves empty; label values are not mixed in. The source is projected to the ontology `Image`
fields `_ont_source_uri` and `_ont_source_revision`. Workloads from
other providers match GitHub container images by digest when their declarative
schemas expose compatible matcher fields.

## Image to repository matching

An image whose provenance (SLSA attestation or an `org.opencontainers.image.source`
label) names a synced repository is linked with `match_method` `provenance`.
Dockerfile analysis is a fallback for images without known provenance. It compares
the image's layer history with each Dockerfile's final stage and needs at least two
similar commands, so a final stage with a single `COPY` does not match on its own.
When the best match ties across repositories, Dockerfile analysis creates no link;
a GHCR image can still be linked to the single repository that owns its package.
Set the OCI source and revision labels on every build, especially for images built
from short Dockerfiles.

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

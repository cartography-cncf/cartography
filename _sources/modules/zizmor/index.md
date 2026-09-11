# Zizmor

The Zizmor module ingests reports produced by
[zizmor](https://github.com/zizmorcore/zizmor), a static analyzer for GitHub
Actions. It attaches the CI supply-chain weaknesses zizmor detects to the
workflows, actions, and repositories already present in the graph.

Cartography's GitHub module records what a workflow is allowed to do (its
triggers, its `permissions` block, the secrets it references, whether the
actions it calls are pinned). Zizmor findings record what is actually wrong
with it. Together they answer questions such as:

- Which workflows are vulnerable to template injection and also run on
  `pull_request_target`?
- Which unpinned actions are used by workflows that can read `contents: write`?
- Which repositories reference an action whose commit does not exist upstream?
- Which findings are being suppressed with `# zizmor: ignore` comments?

## Graph model

`ZizmorFinding` represents one weakness reported by one zizmor audit at one
location. It carries the audit identifier, zizmor's severity, confidence, and
persona determinations, the offending YAML path, and the available fixes.

Findings link to:

- `GitHubWorkflow` via `AFFECTS`, matched on the repository and the
  repository-relative file path.
- `GitHubAction` via `AFFECTS`, but only for findings whose location is a
  `uses` key. A finding reported against a `run` block, a `permissions` block,
  or a workflow trigger has no action to point at.
- `GitHubRepository` via `FOUND_IN`.

Findings also carry the ontology label `SecurityIssue`.

## Finding identity

Zizmor's JSON output has no finding identifier, so Cartography synthesizes one
by hashing five things: the audit id, the repository URL, the file path, the
YAML route of the offending node, and the location's sub-feature component.
That last one is what distinguishes two findings of the same audit inside a
single block, such as two injectable expressions in one `run` step; it is an
offset within the block's own text, not a position in the file.

Line and column numbers are deliberately excluded. An unrelated edit earlier in
the file shifts every line below it, and a finding that only moved should not be
reported as a new one.

Relationship targets are not part of the hash, which is why cleanup removes
stale relationships as well as stale nodes. See below.

## Suppressed findings

A finding suppressed by a `# zizmor: ignore[...]` comment is marked
`ignored = true` and ingested rather than dropped, so that suppressions remain
auditable.

This only works if the report was produced with `--no-ignores`. Without that
flag zizmor omits suppressed findings from its output entirely, so they never
reach the graph and `ignored` is never true. See
[configuration](config.md).

`ignored` reflects comment-based suppression only. A rule disabled through
zizmor's configuration file is reported like any other finding, with
`ignored = false`.

## Cleanup behavior

Stale findings and stale finding relationships are removed per repository.
Relationships are cleaned separately from nodes because a finding's id does not
cover its relationship targets: bumping the action a step calls keeps the same
audit, file path and YAML route, so the finding node survives while its
`AFFECTS` edge moves to the new action.

Cleanup only runs for a repository that was fully observed, meaning every one of
its reports was read and every finding in them could be joined to the graph. A
report that cannot be read, or one holding a finding with no joinable path such
as one read from stdin, leaves that repository's findings in place rather than
deleting them as though they had been fixed. Either way, the other repositories
in the mapping file are still cleaned up normally.

A report that is corrupt past its opening element is rejected outright rather
than partially ingested, for the same reason.

See [configuration](config.md) for setup and input requirements, and the
generated [schema](schema.md) for graph fields and relationships.

```{toctree}
config
schema
```

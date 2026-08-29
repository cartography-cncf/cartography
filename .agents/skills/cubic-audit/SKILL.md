---
name: cubic-audit
description: Audit and improve the cubic AI-review config (`cubic.yaml`) for this repo. Reviews the custom review rules for relevance, scoping, limits, and factual accuracy, then reconciles them against the repo's cubic learnings, promoting the few high-value recurring ones into durable rules and flagging obsolete, duplicate, or contradictory learnings for cleanup (each verified against the live code). Use when asked to "audit cubic", "rework the cubic config", "review the cubic rules", "check cubic learnings", or on a recurring cadence to keep the review config sharp.
---

# cubic-audit

Periodic audit of the cubic AI-review configuration (`cubic.yaml` at the repo root). Two deliverables, in order:

1. **Rule review**: are the custom review rules the highest-signal set for this repo, correctly scoped, within cubic's limits, and factually accurate against the code?
2. **Learnings reconciliation**: which accumulated cubic learnings should be promoted into durable rules, and which are obsolete / duplicate / contradictory and should be cleaned up in the cubic UI.

**Two modes.** Deliverable 2 needs the cubic learnings MCP (tools `list_learnings` / `get_learning`). That server is connected per-account in the cubic app, **not** declared in the repo's `.mcp.json`, so a teammate running this skill may not have it. Probe for it in step 1: if it is reachable, run the **full audit** (both deliverables). If not, run **rules-only mode** (deliverable 1 plus the `cubic.yaml` validation in step 4), and tell the user the learnings reconciliation was skipped because the cubic MCP is not connected, with a one-line pointer on how to enable it (connect the cubic integration in the cubic app, then re-run). Never block the whole skill on the missing MCP.

Cubic docs (re-check if a limit below seems wrong): https://docs.cubic.dev/configure/cubic-yaml and https://docs.cubic.dev/ai-review/custom-agents

**Language:** all output (chat, `cubic.yaml` text, commit messages) is **US English**, regardless of the language used to invoke the skill.

**Open source:** cartography is a public CNCF project. Never reference clients, internal tickets, or private deployments in `cubic.yaml`, commits, or learnings recommendations.

## Hard constraints (bake these in)

- **Max 5 enabled custom rules per repo.** Order matters; beyond the limit only the first N take effect. To add one you must merge or drop one. `cubic.yaml` is already at the cap (5 `custom_rules`), so every "promote" recommendation must name what it merges into or replaces.
- **10,000 characters per rule**, and that budget *includes the resolved content of any `file_paths`*. Attaching a large doc (`AGENTS.md`, a `schema.md`) is counterproductive: it truncates to the least-relevant top and starves the prompt. Prefer self-contained prompts; only link a file if it is small (<2k) and review-focused.
- `cubic.yaml` merges across levels: repo > org > UI > built-in defaults.
- **No MCP tool deletes or edits a learning.** Learnings cleanup is a **manual action in the cubic UI**. This skill produces the list; a human actions it.
- **No em-dashes / en-dashes** anywhere in `cubic.yaml` or commits. Run `grep -n '—\|–' cubic.yaml` before declaring done.
- Honor the repo's worktree/path and git rules in `AGENTS.md` (`CLAUDE.md` may be a symlink to it; read `AGENTS.md` directly). Commit/push only when explicitly asked; commits use `--signoff` (DCO is required on this repo); never open a PR without per-PR authorization.

## Workflow

### 0. Context
- Confirm the repo root (or worktree). Read `cubic.yaml`.
- Derive the GitHub slug: `git remote get-url origin` -> `owner/repo` (this repo: `cartography-cncf/cartography`).

### 1. List learnings (cubic MCP) -- skip if unavailable
The cubic MCP server is namespaced by an opaque id and is connected per-account in the cubic app, not in the repo's `.mcp.json`. **Probe first:** run `ToolSearch` for `list_learnings get_learning cubic`. If it returns no matching tool, the cubic MCP is not connected in this environment: **skip the rest of this step and all of steps 2 and 5's cleanup table**, run rules-only mode (steps 3-4), and state in the report that learnings reconciliation was skipped (connect the cubic integration in the cubic app and re-run to enable it). Do not fabricate learnings from memory.

If the tool is found, call `list_learnings(owner, repo)`.

The result is large and is **persisted to a file** (the tool message returns its path). Do not read it raw. Extract a compact view and **read 100% of it**:

```bash
# f = the persisted list_learnings result file path from the tool message
awk '
/^## / { cat=$0; sub(/^## /,"",cat); next }
/^### / { title=$0; sub(/^### /,"",title); desc=""; getline; while($0=="") getline; while($0!="" && $0 !~ /^- \*\*/){ desc=desc $0 " "; getline } next }
/^- \*\*Confidence\*\*/ { c=$0; sub(/.*: /,"",c) }
/^- \*\*Source\*\*/     { s=$0; sub(/.*: /,"",s) }
/^- \*\*Updated\*\*/    { u=$0; sub(/.*: /,"",u); printf "[%s] %s | %s | %s | %s\n    %s\n", cat, title, c, s, u, desc }
' "$f" > /tmp/cubic_learnings_compact.txt
wc -l /tmp/cubic_learnings_compact.txt
```

Read the compact file fully (chunk it). Never pipe the awk through `head`: it silently drops the tail and you will miss whole categories.

### 2. Bucket the learnings

Most learnings are **negative / suppression** ("Do not flag X", "Treat Y as intentional", "Before flagging Z, check W"). These are false-positive corrections that already apply automatically. **Do NOT turn suppression learnings into rules**: a rule says "flag", a suppression says "do not".

- **Promote candidates**: positive / prescriptive ("always do X"), general, recurring (appears 2+ times or echoes a known convention), and **not already covered** by an existing rule. Expect only 1-3 per audit. Since the config is at the 5-rule cap, each promotion must fold into an existing rule's description rather than add a sixth.
- **Cleanup candidates**:
  - *Contradictory*: conflicts with a rule or with repo reality. Highest priority, since these suppress real findings.
  - *Obsolete*: references a removed/renamed module, deleted helper, or a label/pattern that no longer exists in the code.
  - *Duplicate*: near-identical pairs (often the same rule reworded, or one with a hyphen vs an arrow).
  - *Low-value*: vague entries under ~75% confidence that are platitudes. Optional prune.

**Verify before recommending deletion.** Never trust the learning text alone: grep the code for the referenced symbol / dir / feature. Patterns that pay off:
```bash
git grep -n 'def from_node_schema'             # the signature a rule quotes is correct?
git grep -lI 'aws_handle_regions' -- '*.py'    # decorator still referenced?
ls cartography/intel/<module> 2>/dev/null      # module still exists / not renamed?
```

### 3. Audit the rules themselves
- Are the (<=5) rules the highest-signal for this graph-centric (Neo4j/Cypher) intel tool? Rules tied to the declarative data model (node/rel schemas, MatchLinks, scoped cleanup) and the `get -> transform -> load -> cleanup` sync contract earn their slots; pure-hygiene rules are the first to cut when you need room.
- **Redundant with tooling?** Drop checks already enforced by the pre-commit stack (`black`, `isort`, `flake8`, `pyupgrade`, `mypy`). Example: `pyupgrade --py36-plus` already rewrites legacy `typing.Dict/List/Optional` to PEP 585 builtins, so a rule should not also police that. Inspect `.pre-commit-config.yaml` and the `[flake8]` block in `setup.cfg` before keeping a hygiene rule.
- **Scoping**: every rule should carry `include`/`exclude` globs so it only runs where relevant (cuts false positives, saves the 10k budget). Test-only guidance -> `tests/**`; schema-doc guidance -> `docs/root/modules/**`; AWS-decorator guidance -> `cartography/intel/aws/**`. The existing PII rule already `exclude`s `tests/**` as a model.
- **Factual accuracy**: every helper name / signature / path quoted in a prompt must match the code. Verify with grep (a wrong signature in a prompt produces wrong reviews). Spot-check the claims already baked into `cubic.yaml` (e.g. `GraphJob.from_node_schema()`, `GraphJob.from_matchlink()`, `@timeit`, `@aws_handle_regions`, the `RESOURCE`/`INWARD` sub-resource contract).
- **`ignore.files` (use sparingly)**: `reviews.ignore.files` skips matching files *entirely*, so it removes all review coverage, not just noise. Reserve it for purely machine-generated artifacts with no hand-authored content. Do **not** ignore files that another mechanism already governs or that carry meaningful diffs: in this repo `uv.lock` must stay reviewable because a custom rule flags unwarranted lockfile-only churn (ignoring it disables that signal), and `tests/data/**` are hand-maintained fixtures that `AGENTS.md` lists as part of the intel-module surface. Prefer a scoped custom rule over hiding a file. The current `cubic.yaml` intentionally has no `ignore` block.

### 4. Validate cubic.yaml
```bash
uv run --with pyyaml --no-project python -c "
import yaml
d=yaml.safe_load(open('cubic.yaml')); r=d['reviews']
print('YAML OK | rules:', len(r['custom_rules']), '(max 5)')
for c in r['custom_rules']:
    n=len(c['description']); print(f\"  {n:>5} chars  {c['name']}{'  <-- OVER 10k!' if n>10000 else ''}\")
"
grep -n '—\|–' cubic.yaml && echo 'FIX em/en-dashes' || echo 'no em/en-dashes'
```

### 5. Report, then apply
Present three recap tables and stop for approval before editing:
- **Promote**: learning -> target rule (which existing rule it folds into) -> why.
- **Cleanup** (grouped: contradictory / obsolete / duplicate / low-value): learning -> type -> code-verified justification.
- **Refactor**: rule changes (merge / split / rescope) within the 5 cap.

After approval:
- Apply the `cubic.yaml` edits, then re-run the step-4 validation.
- Hand the learnings cleanup list to the user as **manual cubic-UI actions** (no MCP delete exists).
- Commit/push only if asked; PR only with per-PR authorization. Commit message in US English, with `--signoff`, plus the repo's standard `Co-Authored-By` trailer.

## Notes
- Read-mostly on cubic: this skill lists learnings, never mutates them, and edits only `cubic.yaml`.
- Keep rule prompts self-contained and concrete (good/bad examples + the "why"); that beats terse rules and avoids the `file_paths` truncation trap.

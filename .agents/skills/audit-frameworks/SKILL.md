---
name: audit-frameworks
description: Audit Cartography's rules and compliance frameworks under `cartography/rules/data/rules/`. Surfaces TODOs that the schema can now satisfy, per-provider rules that should collapse into one ontology rule, and duplicate detections across frameworks (CIS, ISO 27001, SOC 2, NIST). Use when the user asks to "audit frameworks", "audit rules", "review rule TODOs", "find duplicate rules", "find ontology candidates", "consolidate compliance frameworks", or "map ISO/SOC2 onto CIS".
---

# audit-frameworks

A read-only audit of `cartography/rules/data/rules/`. Produces a structured report with concrete consolidation proposals; does NOT modify rules unless the user explicitly approves a follow-up.

The audit covers four dimensions:

1. **TODO triage**: every `# TODO: ...` in a rule file annotates a control that could not be implemented at the time. Re-check whether the schema now exposes the missing data.
2. **Cross-provider to ontology**: find rule clusters that have one fact per provider but could collapse into a single fact using ontology semantic labels (`UserAccount`, `Database`, `ObjectStorage`, etc.).
3. **Duplicate rules**: find rules across different framework files that detect the same condition.
4. **Framework consolidation**: when duplicates exist, keep the rule from the most technical framework (CIS, NIST 800-53) and map the compliance frameworks (ISO 27001, SOC 2) onto it via `frameworks=`.

## Critical rules

1. **Audit only**. Emit a report. Do not delete rules, change `__init__.py`, or rewrite Cypher without explicit user confirmation per finding.
2. **Cite file and line for every finding**. The user must be able to jump straight to the code.
3. **Prefer the technical framework**. When consolidating, CIS and NIST 800-53 keep the rule; ISO 27001, SOC 2, PCI DSS get added to that rule's `frameworks` tuple.
4. **Same detection is not the same as same control**. Two rules can share a Cypher pattern but enforce different controls (e.g. encryption-at-rest vs encryption-in-transit). Verify the description and the `WHERE` clause before flagging a duplicate.
5. **Never reference closed-source platforms or tickets** in the audit report or in any rule change. Cartography is open source.

## Inputs

- `cartography/rules/data/rules/`: every `*.py` file is in scope.
- `cartography/rules/data/rules/__init__.py`: registration map.
- `cartography/rules/spec/model.py`: `Rule`, `Fact`, `Framework`, `Module`, `Maturity` definitions.
- `cartography/models/<provider>/`: declarative schema. Drives the TODO triage.
- `cartography/models/ontology/mapping/data/` and `docs/root/modules/ontology/schema.md`: semantic labels and `_ont_*` properties. Drives the ontology-collapse pass.
- `cartography-rules list`, `cartography-rules frameworks`: quick inventory.

## Instructions

### Step 1: inventory

Build a working set before analysing:

```bash
cartography-rules list
cartography-rules frameworks
grep -rn "TODO\|FIXME" cartography/rules/data/rules/
```

For each rule file, record:

- file path
- rule ids declared (`grep -E '^[a-z0-9_]+ = Rule\('`)
- frameworks attached (`grep -A6 'frameworks=' <file>`)
- modules touched (parse `module=Module.<X>` per fact)

Keep this inventory in the working report; later steps refer back to it.

### Step 2: TODO triage

For every TODO comment in scope (typical form: `# TODO: CIS K8s 1.1.1: ...` followed by `# Missing datamodel: <thing>`):

1. **Parse the TODO**: extract the framework, the requirement id, and the "Missing datamodel" / "Missing datamodel or evidence" clause.
2. **Probe the schema** for the named gap. Examples:
   - "Missing datamodel: control plane host filesystem metadata for kube-apiserver manifest files" suggests searching `cartography/models/kubernetes/` for a node with file-permission properties.
   - "Missing datamodel: initContainers and ephemeralContainers securityContext fields" suggests searching `cartography/models/kubernetes/pod.py` and friends for those fields.
3. **Verdict** per TODO:
   - `IMPLEMENTABLE`: schema now exposes the data; propose authoring the rule and link to the `create-rule` skill.
   - `BLOCKED`: schema still lacks the data; record the missing node/property names so the user can prioritise schema work.
   - `OUTDATED`: control is no longer relevant (e.g. CIS revision dropped it); propose deleting the TODO comment.

Do not author the implementable rules in this skill. Hand off to `create-rule`.

### Step 3: cross-provider to ontology candidates

Goal: find rules whose facts repeat the same logic across providers but could be a single ontology fact.

1. **Identify candidate rules**: rules with 2+ facts where each fact targets a different provider node label and the Cypher patterns are structurally similar. Useful starting filter:

   ```bash
   grep -lE "module=Module\.(AWS|AZURE|GCP)" cartography/rules/data/rules/*.py \
     | xargs grep -lE "module=Module\.[A-Z]+" \
     | sort -u
   ```

2. **Check ontology coverage**: for each provider node in the rule's facts, confirm whether it carries a semantic label (`UserAccount`, `Database`, `ObjectStorage`, `FileStorage`, `Tenant`, `DeviceInstance`, etc.) and the `_ont_*` properties referenced in the existing query (typically `_ont_email`, `_ont_source`, `_ont_public`, etc.). If every relevant node is mapped, the rule is a strong collapse candidate.
3. **Output**: for each candidate emit:
   - rule id and file
   - facts that would be replaced
   - proposed ontology Cypher (one fact, `module=Module.CROSS_CLOUD`)
   - any provider-specific facts that should remain (e.g. provider-only attributes the ontology does not normalise)
4. **Defer authoring**: propose, do not write. Hand off to `enrich-ontology` if a node still needs to be mapped.

### Step 4: duplicate detection

Two rules are duplicates when they detect the **same condition on the same asset class**, even if their ids, descriptions, or Cypher differ cosmetically. Cluster candidates by:

1. **Shared Cypher signature**: same `MATCH` labels, same load-bearing `WHERE` predicate (ignoring identifier renames).
2. **Shared output identity field**: both Findings expose the same `asset_id_field` (or equivalent).
3. **Shared remediation intent**: descriptions paraphrase each other.

Useful one-liners:

```bash
# pull every WHERE clause to spot near-duplicates
grep -nE "WHERE " cartography/rules/data/rules/*.py | sort -k2

# group rules by MATCH label
grep -nE "MATCH \([a-z]+:[A-Z]" cartography/rules/data/rules/*.py
```

Report each suspected duplicate as a tuple: `{technical_rule_id, compliance_rule_id, file_paths, evidence}` plus a confidence note (HIGH / MEDIUM / LOW).

### Step 5: consolidation plan

For every HIGH-confidence duplicate cluster:

1. **Pick the keeper** in this priority order: CIS, then NIST 800-53, then NIST CSF / NIST AI RMF, then ISO 27001, then SOC 2, then PCI DSS, then custom. Tie-breaker: the rule with the more specific Cypher and richer Finding.
2. **Plan the merge**:
   - Add the duplicate's `Framework(...)` entries to the keeper's `frameworks=` tuple. Preserve `name`, `short_name`, `scope`, `revision`, `requirement` exactly.
   - Delete the duplicate file or rule symbol.
   - Remove the duplicate's import + registration line from `cartography/rules/data/rules/__init__.py`.
   - If the duplicate had references the keeper lacks, merge them into the keeper's `references=` list.
3. **Sanity check**: keeper's `module` set still covers every provider the duplicate covered. If not, downgrade the merge to "needs an extra fact first" and stop.

Hand the plan to the user as a numbered list. Apply only after explicit confirmation, one cluster at a time.

## Output report format

```
# Cartography rules audit, <YYYY-MM-DD>

## 1. TODO triage
- IMPLEMENTABLE (n)
  - <file>:<line>: CIS K8s 1.1.x. Schema now exposes <Node.property>. Author via the create-rule skill.
- BLOCKED (n)
  - <file>:<line>: needs <Node>/<property>. Suggest opening a schema task.
- OUTDATED (n)
  - <file>:<line>: control dropped in revision X.

## 2. Ontology collapse candidates
- <rule_id> (<file>): facts aws_*, azure_*, gcp_* could become a single Module.CROSS_CLOUD fact using :<SemanticLabel>.

## 3. Duplicate clusters
- HIGH: cis_aws_X (<file>) vs iso27001_Y (<file>): same MATCH(:RDSInstance) WHERE publicly_accessible=true.

## 4. Consolidation plan
1. Keep cis_aws_X. Add Framework(short_name="iso27001", requirement="A.13.1.1", ...). Remove iso27001_Y. Update __init__.py.
2. ...
```

Always end the report with `Recommended next: ...` listing the highest-impact item.

## Examples

### Example: TODO triage hit

User says: `audit the cartography frameworks`.

1. Inventory finds `# TODO: CIS K8s 5.2.6: Partial control coverage. Missing datamodel or evidence: initContainers and ephemeralContainers securityContext fields`.
2. Probe `cartography/models/kubernetes/pod.py` (or related). If `init_containers` is now a property with `security_context` fields, mark `IMPLEMENTABLE`.
3. Report references the new schema fields and points at the `create-rule` skill for authoring.

### Example: ontology collapse

User says: `find rules we can move to ontology only`.

1. Find `database_instance_exposed.py` with three facts (RDS, Azure SQL, Cloud SQL).
2. Confirm all three node types carry the `:Database` semantic label and `_ont_public` property.
3. Propose a single `Module.CROSS_CLOUD` fact: `MATCH (db:Database) WHERE db._ont_public = true RETURN db.id AS id, db._ont_source AS source`.

### Example: duplicate consolidation

User says: `find duplicate rules across frameworks`.

1. `cis_aws_2_1_3` (S3 bucket public) and `iso27001_a_13_1_1_storage_public` both `MATCH (b:S3Bucket) WHERE b.public = true`.
2. Keeper: `cis_aws_2_1_3`. Action: append `Framework(name="ISO/IEC 27001", short_name="iso27001", requirement="A.13.1.1")` to its `frameworks=` tuple, delete `iso27001_a_13_1_1_storage_public`, drop the import from `__init__.py`.
3. Wait for the user's go-ahead before editing.

## Hand-offs

- Authoring a missing rule: `create-rule` skill.
- Mapping a provider node to a semantic label so an ontology collapse becomes possible: `enrich-ontology` skill.
- Adding the missing schema property surfaced by a BLOCKED TODO: `add-node-type` skill.

## Common pitfalls

- **Treating tags as frameworks.** `tags=("compliance", "cis:1.14")` is legacy. Use `frameworks=(Framework(...),)` and keep `tags` for category labels only.
- **Collapsing rules whose facts diverge in `WHERE` semantics.** Public-network exposure and missing-encryption look similar in Cypher but are different controls; do not merge.
- **Dropping the duplicate before updating `__init__.py`.** The CLI inventory will break. Always edit `__init__.py` in the same change.
- **Mapping ISO 27001 to a CIS rule that does not actually satisfy the ISO control.** Read the ISO control text before claiming coverage; partial coverage means keep both rules and add a TODO instead.

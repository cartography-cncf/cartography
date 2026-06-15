---
name: promote-ontology-relationship
description: Promote provider-specific relationships to a canonical cross-provider ontology edge using the WORKLOAD_PARENT pattern (a parallel CartographyRelSchema with the canonical rel_label, the old edge kept and deprecated, plus a RelConstraint enforced by the CI guard). Use when the user asks to "propagate X->Y relationship to the ontology level", unify/normalise a relationship label across providers, add a canonical ontology edge (HAS_ROLE, MEMBER_OF, ASSUMES, ENCRYPTED_BY, POINTS_TO, ...), add a RelConstraint, or deprecate/rename an ontology relationship label.
---

# promote-ontology-relationship

Cartography normalises cross-provider edges between two **ontology-labelled** nodes (semantic labels like `UserAccount`, `PermissionRole`, `ServiceAccount`, `ComputePod`, or abstract nodes like `User`, `Device`) under a single canonical relationship label. The canonical label is declared as a `RelConstraint` and enforced by a CI guard.

There are two cases. **(A) A direct provider edge already exists** between the two ontology-labelled nodes: promote it in place, following the `WORKLOAD_PARENT` precedent (PRs #2735 / #2738): add a parallel canonical edge, keep the old one deprecated for backward compatibility, and add a constraint. This promotion is **NOT** done with analysis/linking jobs. **(B) No direct edge exists yet** (the relationship only lives through a binding node, or in another sync's data, or not at all): you must *create* the canonical edge, choosing the cheapest mechanism that fits (see [When no direct edge exists](#when-no-direct-edge-exists-genuine-gap)). In both cases the canonical label is still declared as a `RelConstraint` and enforced by the guard.

## Mechanism (the WORKLOAD_PARENT pattern)

For each existing **direct** `CartographyRelSchema` edge that connects two ontology-labelled nodes:

1. **Add a new parallel rel class** with `rel_label = "<CANONICAL>"`, same `target_node_label` / matcher / direction as the existing edge, and register it in the node schema's `other_relationships` (both edges MERGE on every sync).
2. **Keep the old edge** but mark it `# DEPRECATED: replaced by <CANONICAL>, will be removed in v1.0.0`, and add its rel class to `LEGACY_REL_WHITELIST` in [`constraints.py`](../../../cartography/models/ontology/constraints.py).
3. **Add a `RelConstraint(src, dst, label)`** to `ONTOLOGY_REL_CONSTRAINTS` so the guard enforces the canonical label + direction whenever both endpoints carry the listed ontology labels.
4. **Whitelist** any other existing edge that shares the same ontology-label pair but carries a *distinct semantic* (reverse direction, or a different concept).

If a provider already uses the chosen canonical label, that edge is already compliant: leave it untouched (no parallel, no deprecation).

## When no direct edge exists (genuine gap)

Sometimes a constrained pair has **no direct provider edge** to promote: the relationship only exists through a binding node (`AWSInstanceProfile`, `AzureRoleAssignment`), or the two endpoints are created in different syncs, or the data simply is not modelled yet. The constraint still belongs in `constraints.py` (it never requires the edge to exist), but to actually populate the edge you *create* it. Pick the cheapest mechanism that fits, in this strict priority order:

1. **Classic `CartographyRelSchema` (preferred).** Use when the source node's own payload already carries the target's identifier (e.g. an AWS Lambda payload holds its execution-role arn, an API-key payload holds its owner id). Add a normal rel class on the source schema pointing at the target label, with the canonical `rel_label`. This is just Step 4 without a deprecated sibling. Use the `add-relationship` skill for the mechanics.

2. **MatchLink — always prefer this over an analysis job.** Use when the two endpoints are created in **different syncs**, or the relationship is only derivable by resolving a binding node, so neither schema's payload can express it directly (e.g. `EC2Instance -[:ASSUMES]-> AWSRole` resolved through the instance profile in the IAM sync; `AzureVirtualMachine -[:ASSUMES]-> AzureRoleDefinition` joined on the managed-identity `principalId` via `AzureRoleAssignment`). Assemble the `(source_key, target_key)` pairs in the owning sync and load them with `load_matchlinks` / a `MatchLink` schema carrying the canonical `rel_label`. The guard reads a MatchLink's direction + label too, so the canonical name is enforced. Use the `add-relationship` skill for `MatchLink` mechanics.

3. **Analysis job (last resort).** Only when the edge is purely **transitive** and the join genuinely cannot be assembled inside a single sync, so it must be computed post-sync by traversing the whole graph (e.g. deriving `GCPInstance -[:ASSUMES]-> GCPRole` across `RUNS_AS` + `HAS_ROLE`, where the compute sync and the IAM-policy-binding sync each hold only half the path). Add a Cypher analysis job (see the `analysis-jobs` skill) that `MERGE`s the canonical edge. If you reach for this, first re-confirm a MatchLink really cannot assemble the pairs; an analysis job is harder to test and to keep idempotent.

Whichever you pick, the canonical label/direction must match the `RelConstraint`, and the edge gets the same docs + integration-test treatment as a promoted edge. Edges through binding nodes are still **not** "direct" for the purposes of Step 3 — they are gaps, handled here.

## Critical rules

1. **The guard reads labels from the node *schema*** (`label` + `extra_node_labels`, including `ConditionalNodeLabel`), not from the runtime graph. An edge is only constrained when **both** endpoints carry an ontology label in their schema. Edges through intermediate binding nodes (e.g. `GCPPolicyBinding`, `KubernetesRoleBinding`, `AzureRoleAssignment`) are NOT direct and are not affected by a rename.
2. **Pick the canonical verb to fit the abstraction, not one provider.** The label applies to the abstract semantic pair (e.g. `UserAccount -> PermissionRole`), which spans many providers. Prefer a neutral verb (`HAS_ROLE`, not `ASSUME_ROLE`, when the target generalises IAM roles, permission sets, and SaaS roles). Reserve action verbs (`ASSUMES`) for workload-identity/runtime semantics.
3. **Backward compatibility is mandatory.** Never rename in place. The old edge keeps being created (whitelisted) until v1.0.0 so existing queries/rules keep working.
4. **Run the guard test to discover collisions**: do not assume you found every edge by reading code. `test_ontology_rel_constraints.py` will list every offending rel (wrong label or reverse direction). Decide per edge: migrate (parallel + deprecate) or whitelist (distinct semantic).
5. **Docs: replace the deprecated relation, do not just annotate it.** In the module `schema.md`, the old edge must be **removed entirely** (bullet + cypher block + mermaid line) and replaced by the canonical one. Do NOT keep it with an inline `(DEPRECATED: ...)` marker: that is the mistake the original `WORKLOAD_PARENT` migration made, and it leaves the duplicate documented. The class stays in code (whitelisted) but is no longer advertised. Add the canonical edge to the ontology `schema.md`.
6. **Decouple internal queries from the deprecated label.** If any analysis job / intel query traverses the old label, switch it to the canonical one (both edges exist, so it is equivalent and survives the v1.0.0 removal).
7. **One commit per canonical edge.** `--signoff`. No internal ticket or client references in committed text.

## Instructions

### Step 1: Identify the canonical pair and label

Decide the abstract pair and verb, e.g. `UserAccount -[:HAS_ROLE]-> PermissionRole`. Confirm the chosen verb is not already overloaded by a different concept (grep the canonical label across the repo).

### Step 2: Find which provider nodes carry each ontology label

The semantic label is applied via `extra_node_labels` on the node schema (sometimes a `ConditionalNodeLabel`). The ontology mapping files under `cartography/models/ontology/mapping/data/<category>.py` list which provider node labels belong to a category. Build the set of node labels carrying `src` and `dst`.

```bash
# which schemas declare the semantic labels
grep -rln '"PermissionRole"' cartography/models/ | grep -v ontology/mapping
grep -rln '"UserAccount"'    cartography/models/ | grep -v ontology/mapping
```

### Step 3: Find the direct edges to migrate

For each `dst` node label, find `CartographyRelSchema` classes whose `target_node_label` is that label (or rels defined on the `dst` schema pointing back at a `src` node). A direct edge is one whose **other endpoint also carries an ontology label**. Edges through binding/intermediate nodes are out of scope (they are not direct).

```bash
grep -rn "target_node_label.*<RoleNodeLabel>" cartography/models/
```

Classify each direct edge:
- **Same label as canonical** -> already compliant, leave it.
- **Different label, canonical direction** -> migrate (Step 4).
- **Different label, reverse direction, or distinct semantic** -> whitelist (Step 6).

### Step 4: Add the parallel canonical edge

In the provider model file, add a Properties + Rel class mirroring the existing one but with the canonical `rel_label`, and register it in `other_relationships`. Mark the old rel deprecated. Example (AWS SSO user -> permission set):

```python
@dataclass(frozen=True)
# DEPRECATED: replaced by the canonical (:UserAccount)-[:HAS_ROLE]->(:PermissionRole)
# edge (AWSSSOUserToPermissionSetHasRoleRel). Kept for backward compatibility,
# will be removed in v1.0.0.
class AWSSSOUserToPermissionSetRel(CartographyRelSchema):
    target_node_label: str = "AWSPermissionSet"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"arn": PropertyRef("AssignedPermissionSets", one_to_many=True)},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "HAS_PERMISSION_SET"
    properties: AWSSSOUserToPermissionSetRelProperties = AWSSSOUserToPermissionSetRelProperties()


@dataclass(frozen=True)
class AWSSSOUserToPermissionSetHasRoleRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# Canonical ontology edge: (:UserAccount)-[:HAS_ROLE]->(:PermissionRole)
class AWSSSOUserToPermissionSetHasRoleRel(CartographyRelSchema):
    target_node_label: str = "AWSPermissionSet"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"arn": PropertyRef("AssignedPermissionSets", one_to_many=True)},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "HAS_ROLE"
    properties: AWSSSOUserToPermissionSetHasRoleRelProperties = AWSSSOUserToPermissionSetHasRoleRelProperties()
```

Then add `AWSSSOUserToPermissionSetHasRoleRel()` to the node schema's `OtherRelationships([...])`.

For edges created in a hand-written query (not a schema rel), add a parallel `MERGE` of the canonical edge next to the existing one, keeping both.

### Step 5: Add the constraint

In [`cartography/models/ontology/constraints.py`](../../../cartography/models/ontology/constraints.py), append to `ONTOLOGY_REL_CONSTRAINTS`:

```python
# A user account is granted a role.
RelConstraint(src="UserAccount", dst="PermissionRole", label="HAS_ROLE"),
```

A constraint with no current direct edge is valid governance ("never requires the edge to exist; only constrains the name when both endpoints carry the labels").

### Step 6: Run the guard, then whitelist remaining collisions

```bash
uv run pytest tests/unit/cartography/graph/test_ontology_rel_constraints.py -q
```

The guard lists violations as either *wrong label* (canonical direction) or *wrong direction* (reverse). For each:
- A deprecated edge you are replacing -> add its class to `LEGACY_REL_WHITELIST` with a `# DEPRECATED: replaced by <CANONICAL>` comment.
- A genuinely different semantic sharing the label pair -> add it to `LEGACY_REL_WHITELIST` with a comment explaining why it is distinct (e.g. `ALLOWED_BY` = "role is assumable by", `MAPS_TO` = identity federation, `ASSUMED_ROLE_WITH_SAML` = runtime event, `ASSUMES_ROLE` = workload identity / IRSA).

Re-run until green. Add the needed imports to `constraints.py` (isort will order them).

### Step 7: Update documentation

**Module `schema.md`** (`docs/root/modules/<provider>/schema.md`): **remove** the deprecated edge and document only the canonical one.

- Delete the relationship bullet, its cypher fenced block, **and** its line in the module's mermaid diagram. Do not leave an inline `(DEPRECATED: ...)` note: the deprecated edge must disappear from the doc entirely.
- The same edge is usually documented in **both endpoints' sections** (e.g. once under the source node, once under the target node) and sometimes in a catch-all list. Grep every occurrence:
  ```bash
  grep -rn "OLD_LABEL\|<SrcNode>.*<DstNode>" docs/root/modules/<provider>/schema.md
  ```
- **Do not remove a same-label edge that is a different, non-deprecated relationship.** Cross-check against `LEGACY_REL_WHITELIST`: only the exact `(src, label, dst)` triples you deprecated are removed. Example from the `WORKLOAD_PARENT` cleanup: `(:ECSService)-[:HAS_TASK]->(:ECSTask)` was removed, but `(:ECSContainerInstance)-[:HAS_TASK]->(:ECSTask)` (same `HAS_TASK` label, not deprecated) was kept. Likewise the Kubernetes namespace catch-all kept `CONTAINS` to `Secret`/`Service`/`Role` and only dropped `Pod`/`Container`.
- Reword surrounding prose/notes to the canonical label.

**Ontology `schema.md`** (`docs/root/modules/ontology/schema.md`): add the edge to the top mermaid diagram (`UA -- HAS_ROLE --> PR`) and to the prose under the `dst` semantic-label section.

### Step 8: Decouple internal queries

Grep the old label across `cartography/` (intel, `data/jobs/`, `rules/`). Any analysis/intel query that traverses the old label should be switched to the canonical one (both exist now). Confirm no rule depends on the old label.

```bash
grep -rn "OLD_LABEL" cartography/intel cartography/data/jobs cartography/rules
```

### Step 9: Tests and verification

Add **additive** assertions in the affected integration tests (assert the new canonical edge; keep the old assertion only if you still assert the deprecated edge intentionally).

```bash
uv run pytest tests/unit/cartography/graph/test_ontology_rel_constraints.py -q
uv run pytest tests/integration/cartography/intel/<provider>/ -q   # needs Neo4j
uv run --frozen pre-commit run --files <changed files>
```

## Reference

- `references/worked-example.md`: the full `HAS_ROLE` migration: every file touched, the collisions the guard surfaced, and how each was resolved.

## Related skills

- `add-relationship`: base `CartographyRelSchema` / `MatchLink` mechanics.
- `enrich-ontology`: applying the semantic labels (`extra_node_labels`, `_ont_*`) that this skill's constraints operate on.
- `analysis-jobs`: when an edge must be derived after sync rather than declared on a schema.

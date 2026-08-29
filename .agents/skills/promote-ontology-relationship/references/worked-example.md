# Worked example: `HAS_ROLE` (UserAccount/ServiceAccount -> PermissionRole)

This is the real migration that introduced the canonical `HAS_ROLE` edge, done as two commits (the user edge, then the service-account constraint).

## Goal

- `(:UserAccount)-[:HAS_ROLE]->(:PermissionRole)`
- `(:ServiceAccount)-[:HAS_ROLE]->(:PermissionRole)`

`PermissionRole` is the semantic label on AWS roles/permission sets, Azure role definitions, GCP roles, Keycloak/Cloudflare/OCI/Okta/Kubernetes roles, etc. `HAS_ROLE` was chosen over `ASSUME_ROLE` because the target generalises **permission sets** (static assignment) and SaaS roles, where "assume" is semantically wrong. `ASSUME_ROLE`/`ASSUMES` stays reserved for workload-identity (STS / IRSA).

## Direct edges found (Step 3)

| Provider  | Edge                                                              | Old label            | Action                              |
| --------- | ----------------------------------------------------------------- | -------------------- | ----------------------------------- |
| AWS       | `AWSSSOUser -> AWSPermissionSet` (`awsssouser.py`)                | `HAS_PERMISSION_SET` | add parallel `HAS_ROLE`, deprecate  |
| Keycloak  | `KeycloakUser -> KeycloakRole` (INWARD on `KeycloakRoleToUserRel`)| `ASSUME_ROLE`        | add parallel `HAS_ROLE`, deprecate  |
| Cloudflare| `CloudflareMember -> CloudflareRole` (`member.py`)                | `HAS_ROLE`           | already compliant: untouched       |

Service-account -> role: no **direct** edge exists (GCP/K8s/Azure go through binding nodes); the constraint is added as forward-looking governance.

The Keycloak group-inherited edge is created in a hand-written query (`cartography/intel/keycloak/inheritance.py` `_ASSUME_ROLE_VIA_GROUP_QUERY`): a parallel `MERGE (u)-[:HAS_ROLE]->(r)` was added next to the existing `ASSUME_ROLE` merge.

## Collisions the guard surfaced (Step 6) and their resolution

Running `test_ontology_rel_constraints.py` after adding the constraints flagged edges sharing the `UserAccount|ServiceAccount` / `PermissionRole` label pair. Each was whitelisted with a reason, because it is a *distinct* semantic, not a static role grant:

| Rel class                          | Label                   | Why whitelisted (not migrated)                                  |
| ---------------------------------- | ----------------------- | --------------------------------------------------------------- |
| `AWSSSOUserToPermissionSetRel`     | `HAS_PERMISSION_SET`    | the edge we deprecated                                          |
| `KeycloakRoleToUserRel`            | `ASSUME_ROLE`           | the edge we deprecated                                          |
| `CloudflareMemberToCloudflareRoleRel` | `HAS_ROLE`           | (not whitelisted: it IS the canonical edge)                    |
| `AWSRoleToSSOUserMatchLink`        | `ALLOWED_BY`            | reverse direction; "role is assumable by SSO user", not a grant |
| `KubernetesUserToAWSRoleRel`       | `MAPS_TO`               | identity-federation mapping, not a grant                        |
| `AssumedRoleWithSAMLMatchLink`     | `ASSUMED_ROLE_WITH_SAML`| CloudTrail-observed runtime assumption event                    |
| `KubernetesServiceAccountToAWSRoleRel` | `ASSUMES_ROLE`      | workload-identity (IRSA); reserved for the `ASSUMES` edge        |

Lesson: a constraint catches **every** edge between the two labels, including reverse-direction MatchLinks and unrelated concepts. Read code first, but trust the guard to find the rest.

## Files touched

Commit 1 (`HAS_ROLE` user edge):
- `cartography/models/ontology/constraints.py`: `RelConstraint(UserAccount, PermissionRole, HAS_ROLE)` + whitelist entries + imports
- `cartography/models/aws/identitycenter/awsssouser.py`: parallel `HAS_ROLE` rel, deprecate old
- `cartography/models/keycloak/role.py`: parallel `HAS_ROLE` rel, deprecate old
- `cartography/intel/keycloak/inheritance.py`: parallel `HAS_ROLE` MERGE in the group-inherited query; **and** switched `_ASSUME_SCOPE_QUERY` to traverse `HAS_ROLE` (decouple from the deprecated label)
- `docs/root/modules/aws/schema.md`, `docs/root/modules/keycloak/schema.md`, `docs/root/modules/keycloak/analysis.md`: document only `HAS_ROLE` (deprecated edge removed from docs)
- `docs/root/modules/ontology/schema.md`: `UA -- HAS_ROLE --> PR` + prose
- `tests/integration/.../aws/test_identitycenter.py`, `tests/integration/.../keycloak/test_roles.py`: additive `HAS_ROLE` assertions

Commit 2 (`HAS_ROLE` service-account constraint):
- `cartography/models/ontology/constraints.py`: `RelConstraint(ServiceAccount, PermissionRole, HAS_ROLE)` + whitelist `KubernetesServiceAccountToAWSRoleRel`
- `docs/root/modules/ontology/schema.md`: `SA -- HAS_ROLE --> PR` + prose

## Verification used

```bash
uv run pytest tests/unit/cartography/graph/test_ontology_rel_constraints.py tests/unit/cartography/test_doc.py -q
uv run pytest tests/integration/cartography/intel/aws/test_identitycenter.py \
              tests/integration/cartography/intel/keycloak/ \
              tests/integration/cartography/intel/cloudflare/test_members.py -q
uv run --frozen pre-commit run --files <changed files>
```

# IAM `managed_type` Classification — Implementation Plan

## Goal

Classify every IAM resource synced by Cartography as **provider-created** vs
**customer-created** using a single, standard node property:

| Field | Values | Meaning |
|-------|--------|---------|
| `managed_type` | `"predefined"` | Created/owned by the cloud provider (built-in roles, AWS-managed policies, Google default service accounts, Oracle root compartment, etc.) |
| `managed_type` | `"custom"` | Created by a customer/principal in the tenant |

Scope: **all** IAM node types in each provider's `intel/<provider>/iam.py`
(plus `intel/oci/compartment.py`). Types that have a genuine provider-managed
variant are classified by a concrete rule; types with no provider variant
(human users, customer groups, app registrations) default to `"custom"` so the
field is **never null** — downstream needs no null-handling.

## Why a new field name (`managed_type`)

`type` is already overloaded in the IAM domain and cannot carry this meaning
cleanly:

- **AWS** policy nodes: `type` = `managed` / `inline` (`PolicyType` enum).
- **AWS / GCP** role nodes: `type` = `predefined` / `custom` (today's partial impl).
- **Azure** role nodes: `type` = `Microsoft.Authorization/roleDefinitions` (raw API type).
- **Azure** role nodes also carry `role_owner_type` = `predefined`/`custom`.

Reusing `type` would collide on policies and Azure roles. `managed_type` is a
new, unambiguous field set uniformly on every IAM node. Existing fields
(`type` on AWS/GCP roles, `role_owner_type` on Azure roles) are **kept as-is**
for backward compatibility; `managed_type` becomes the canonical field that
downstream should read.

---

## Current state (audit)

| Provider | File | Classification today | Ingestion pattern |
|----------|------|----------------------|-------------------|
| AWS | `cartography/intel/aws/iam.py` | Roles only: `type`=predefined/custom via Path (`/aws-service-role/`, `/service-role/`, `/aws-reserved/`, sso). Managed policies, users, groups: none. | Inline Cypher in `load_*()` |
| GCP | `cartography/intel/gcp/iam.py` | Roles only: `type`=predefined/custom passed into `transform_roles()` (3 separate API fetches). SAs/keys/api-keys: none. | Inline Cypher in `load_*()` |
| Azure | `cartography/intel/azure/iam.py` | Roles only: `role_owner_type`=predefined/custom (BuiltInRole flag). All other principals: none. | Inline Cypher in `_load_*_tx()` |
| OCI | `cartography/intel/oci/iam.py`, `compartment.py` | None at all. | Raw `neo4j_session.run()` with `$PARAM` substitution |

No `cartography/models/<provider>/...iam` schema files exist for any of these —
all node properties are declared inline in `SET` clauses, so changes are local
to the `iam.py` files (and `oci/compartment.py`).

---

## Design rules per provider/resource

Below, "set in transform" = compute `managed_type` on the dict before the load
call; "set in Cypher" = add `node.managed_type = ...` to the `SET` clause.

### AWS — `cartography/intel/aws/iam.py`

| Resource | Rule for `predefined` | Else | Where |
|----------|----------------------|------|-------|
| **Roles** | Existing logic: Path contains `/aws-service-role/`, `/service-role/`, `/aws-reserved/`, or sso-reserved path | `custom` | Mirror existing `role["type"]` block (~L312–322): also set `role["managed_type"]`. Add `rnode.managed_type` in `load_roles()` (~L653) |
| **Managed policies** (account-level) | Policy ARN starts with `arn:aws:iam::aws:policy/` (AWS-managed). Equivalent signal: `Scope == "AWS"` from `list_policies`. | `custom` (customer-managed, ARN has account id) | `transform_policies_data()` (~L253); add `p.managed_type` in `_load_policies_for_account_tx()` (~L560) |
| **Inline policies** | n/a — always | `custom` | `_load_policy_tx()` inline branch (~L943): set literal `custom` |
| **Users** | n/a — AWS has no provider-managed users | `custom` | `load_users()` Cypher (~L446) |
| **Groups** | n/a | `custom` | `load_groups()` Cypher (~L602) |
| **Service accounts** (if loaded) | n/a | `custom` | `load_service_accounts()` (~L489) |

Note: AWS service-linked roles are already covered by the role Path rule.

### GCP — `cartography/intel/gcp/iam.py`

| Resource | Rule for `predefined` | Else | Where |
|----------|----------------------|------|-------|
| **Roles** | Already classified: `type` param = `'predefined'` (from `iam.roles().list()`) vs `'custom'` (project/org custom). | `custom` | `transform_roles()` (~L207): set `role['managed_type'] = type` alongside `role['type']`. Add `u.managed_type = d.managed_type` in `load_project_roles()` (~L542) and `load_sso_roles()` (~L578) |
| **Service accounts** | Email matches a Google-managed pattern: `*-compute@developer.gserviceaccount.com`, `*@appspot.gserviceaccount.com`, `*@cloudservices.gserviceaccount.com`, `*@<service>.iam.gserviceaccount.com` Google service-agents, `service-*@gcp-sa-*.iam.gserviceaccount.com` | `custom` (user-created SAs) | `transform_service_accounts()` (~L52); add `u.managed_type` in `load_service_accounts()` (~L452) |
| **Service account keys** | `keyType == "SYSTEM_MANAGED"` (Google-rotated) | `custom` (`USER_MANAGED`) | `keyType` already loaded as `u.keytype` (L498). Map in transform/load_service_account_keys |
| **API keys** | n/a | `custom` | `load_api_keys()` (~L416) |
| **Users / Groups / Domains** (from bindings) | n/a — external identities | `custom` | `load_*` for binding identity nodes (~L835/L992/L1089) |

### Azure — `cartography/intel/azure/iam.py`

| Resource | Rule for `predefined` | Else | Where |
|----------|----------------------|------|-------|
| **Roles** | Existing logic: `role_type == "BuiltInRole"` or `type == "Microsoft.Authorization/roleDefinitions"` | `custom` | Mirror block at ~L1107–1112: set `role["managed_type"]` next to `role["role_owner_type"]`. Add `i.managed_type` in `_load_roles_tx()` (~L1193) |
| **Service principals** | First-party Microsoft SP: `app_owner_organization_id == "f8cdef31-a31e-4b4a-93e4-5f571e91255a"` (Microsoft tenant), or `service_principal_type == "ManagedIdentity"`/Microsoft-owned built-in apps | `custom` | `app_owner_organization_id` + `service_principal_type` already captured (L910/L922). Compute in transform/load (`load_tenant_service_accounts`) |
| **Managed identities** | n/a — customer-owned | `custom` | `_load_*` for `AzureManagedIdentity` (~L1236) |
| **Users / Groups / Applications / Domains** | n/a | `custom` | respective `_load_*_tx()` |

Keep `role_owner_type` for back-compat; `managed_type` mirrors it.

### OCI — `cartography/intel/oci/iam.py` + `compartment.py`

Raw-Cypher pattern: compute `managed_type` in the `sync_*` / `get_*_list_data`
loop, pass as `MANAGED_TYPE=...`, add `node.managed_type = $MANAGED_TYPE` to the
`SET` clause.

| Resource | Rule for `predefined` | Else | Where |
|----------|----------------------|------|-------|
| **Compartments** | Root compartment (`ocid == tenancy_id`) or name `ManagedCompartmentForPaaS` (Oracle-created) | `custom` | `load_oci_compartments()` (`compartment.py` ~L91), `load_compartments()` (`iam.py` ~L65) |
| **Groups** | Oracle-seeded `Administrators` group (created at tenancy provisioning) | `custom` | `load_groups()` (~L172) |
| **Policies** | Oracle-seeded tenancy policies — `Tenant Admin Policy`, `PSM-*`, root-policy by name in root compartment | `custom` | `load_policies()` (~L275) |
| **Users** | n/a — human/principals | `custom` | `load_users()` (~L96) |
| **Regions** | n/a — Oracle defines regions; treat subscription records as | `predefined` | `load_region_subscriptions()` (~L420) |

OCI cleanup jobs in `cartography/data/jobs/cleanup/oci_import_*.json` need no
change (they match on `lastupdated`), but verify the new property doesn't break
any `RETURN`/index assumptions.

---

## Implementation steps

1. **Shared convention**
   - Decide a single literal pair: `"predefined"` / `"custom"`. No enum class
     required, but optionally add a small constant (e.g. `MANAGED_TYPE_PREDEFINED`,
     `MANAGED_TYPE_CUSTOM`) per provider module for grep-ability.

2. **AWS** (`intel/aws/iam.py`)
   - Roles: add `managed_type` mirroring existing `type` decision.
   - Managed policies: derive from ARN prefix / `Scope`; thread into
     `_load_policies_for_account_tx()`.
   - Inline policies, users, groups, service accounts: set literal `custom`.

3. **GCP** (`intel/gcp/iam.py`)
   - Roles: `role['managed_type'] = type` in `transform_roles()`; add to both role
     load Cyphers.
   - Service accounts: add email-pattern helper `gcp_sa_is_google_managed(email)`.
   - SA keys: map `keyType`.
   - API keys / binding identities: literal `custom`.

4. **Azure** (`intel/azure/iam.py`)
   - Roles: add `managed_type` mirroring `role_owner_type`.
   - Service principals: add first-party detection helper.
   - All other principals/identities/domains: literal `custom`.

5. **OCI** (`intel/oci/iam.py`, `compartment.py`)
   - Add `managed_type` computation + `$MANAGED_TYPE` param to each ingest:
     compartments, groups, policies, users, regions.
   - Helpers: `is_root_compartment(ocid, tenancy_id)`, name-based Oracle-seed
     checks for groups/policies.

6. **Indexes / schema docs**
   - Check `cartography/data/indexes.cypher` (or equivalent) — add an index on
     `managed_type` only if downstream filters on it at scale (optional).
   - Update any node-schema docs under `docs/schema/` that enumerate IAM node
     properties.

7. **Tests**
   - Unit tests per provider asserting `managed_type` on representative fixtures:
     - AWS: a service-linked role → predefined; a customer role → custom; an
       `arn:aws:iam::aws:policy/...` → predefined; account policy → custom.
     - GCP: `roles/viewer` → predefined; `projects/.../roles/x` → custom;
       compute-default SA → predefined; user SA → custom; SYSTEM_MANAGED key → predefined.
     - Azure: BuiltInRole → predefined; CustomRole → custom; Microsoft-tenant SP → predefined.
     - OCI: root compartment → predefined; `Administrators` group → predefined;
       a created policy → custom.
   - Follow existing test layout under `tests/unit/cartography/intel/<provider>/`.

8. **Backward compatibility**
   - Keep `type` (AWS/GCP roles) and `role_owner_type` (Azure roles) untouched.
   - Document that `managed_type` is the canonical, cross-provider field; old
     fields may be deprecated in a later pass.

---

## Downstream contract

After this change, any IAM node across AWS/GCP/Azure/OCI can be filtered with a
single uniform predicate:

```cypher
MATCH (n)
WHERE n.managed_type = 'custom'      // customer-created IAM resources, any cloud
RETURN n
```

No per-provider field knowledge, no null checks.

---

## Open items / verify during implementation

- AWS: confirm `Scope` is present in `list_policies` response in this codebase;
  if not, rely on ARN prefix (`arn:aws:iam::aws:policy/`).
- GCP: finalize the Google-managed SA email pattern list (service-agents domains
  evolve); centralize in one helper.
- Azure: confirm the Microsoft first-party tenant id constant and whether
  `ManagedIdentity` SPs should be predefined or custom (recommendation: custom,
  since the customer creates the identity).
- OCI: enumerate the full set of Oracle-seeded group/policy names beyond
  `Administrators` / `Tenant Admin Policy` for the tenancies you target.
- Line numbers above are current-state references and will drift; locate by
  function name.

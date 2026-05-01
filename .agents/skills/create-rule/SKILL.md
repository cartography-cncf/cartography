---
name: create-rule
description: Author a Cartography security rule (one or more Cypher Facts plus a Pydantic Finding output model) under `cartography/rules/data/rules/`. Use when the user asks to add a security check, detection, attack-surface query, compliance control, CIS benchmark rule, or cross-cloud detection.
---

# create-rule

Cartography rules detect attack surfaces, security gaps, and compliance issues across the graph. Rules are composed of one or more Facts (Cypher queries) and a Finding output model (Pydantic).

## Architecture

```
Rule (e.g., "database-exposed")
  ├─ Fact (e.g., "aws-rds-public")
  ├─ Fact (e.g., "azure-sql-public")
  └─ Fact (e.g., "gcp-cloudsql-public")
```

- **Rule** — represents a security issue / attack surface.
- **Fact** — single Cypher query that gathers evidence.
- **Finding** — Pydantic model defining the result row structure.

## Critical rules

1. **`cypher_query` aliases must match `Finding` field names exactly.** Use `RETURN x.id AS id, x.name AS name`.
2. **`cypher_visual_query` returns nodes**, not properties — used for graph viz.
3. **All `Finding` fields are `| None` with default `None`.** The `source` field is auto-populated.
4. **Compliance metadata uses `frameworks=`**, not tags. Keep `tags` for categories only (`iam`, `credentials`, `stride:*`).
5. **CIS rule names and IDs must include the provider** (e.g. `cis_aws_1_14_...`, not `cis_1_14_...`).

## Instructions

### Step 1 — Imports

```python
from cartography.rules.spec.model import (
    Fact,
    Finding,
    Framework,
    Maturity,
    Module,
    Rule,
    RuleReference,
)
```

### Step 2 — Author Facts

A Fact is a Cypher query that detects one specific condition:

```python
_aws_public_databases = Fact(
    id="aws-rds-public",
    name="Publicly accessible AWS RDS instances",
    description="AWS RDS databases exposed to the internet",
    cypher_query="""
    MATCH (db:RDSInstance)
    WHERE db.publicly_accessible = true
    RETURN db.id AS id, db.db_instance_identifier AS name, db.region AS region
    """,
    cypher_visual_query="""
    MATCH (db:RDSInstance)
    WHERE db.publicly_accessible = true
    RETURN db
    """,
    cypher_count_query="""
    MATCH (db:RDSInstance)
    RETURN COUNT(db) AS count
    """,
    module=Module.AWS,
    maturity=Maturity.STABLE,
)
```

**Fact fields:**

| Field                | Required | Notes                                                      |
| -------------------- | :------: | ---------------------------------------------------------- |
| `id`                 | Yes      | lowercase + hyphens                                        |
| `name`               | Yes      | human-readable                                             |
| `description`        | Yes      | what this fact detects                                     |
| `cypher_query`       | Yes      | structured rows; `AS` aliases match Finding fields         |
| `cypher_visual_query`| Yes      | returns nodes for visualization                            |
| `cypher_count_query` | Yes      | total assets evaluated; `RETURN COUNT(...) AS count`       |
| `module`             | Yes      | `Module.AWS`, `Module.AZURE`, `Module.GCP`, ...            |
| `maturity`           | Yes      | `Maturity.EXPERIMENTAL` or `Maturity.STABLE`               |
| `asset_id_field`     | No       | finding field that uniquely identifies an asset (dedupe)   |

### Step 3 — Define the Finding output model

```python
class DatabaseExposedOutput(Finding):
    """Output model for publicly exposed databases."""
    id: str | None = None
    name: str | None = None
    region: str | None = None
```

- Inherit from `Finding`.
- Field names must match `cypher_query` aliases **exactly**.
- All fields are `| None` with default `None`.
- The `source` field is auto-populated with the module name.

### Step 4 — Compose the Rule

```python
database_exposed = Rule(
    id="database-exposed",
    name="Publicly Accessible Databases",
    description="Detects databases exposed to the internet across cloud providers",
    output_model=DatabaseExposedOutput,
    tags=("infrastructure", "attack_surface", "database"),
    facts=(_aws_public_databases, _azure_public_databases, _gcp_cloudsql_public),
    version="1.0.0",
)
```

**Rule fields:**

| Field          | Required | Notes                                         |
| -------------- | :------: | --------------------------------------------- |
| `id`           | Yes      | lowercase + underscores                        |
| `name`         | Yes      | human-readable                                 |
| `description`  | Yes      | what security issue this detects               |
| `output_model` | Yes      | Pydantic model class                           |
| `tags`         | Yes      | tuple of categorisation tags (no compliance)   |
| `facts`        | Yes      | tuple of `Fact` objects                        |
| `version`      | Yes      | semantic version string                        |
| `references`   | No       | list of `RuleReference` for documentation      |
| `frameworks`   | No       | tuple of `Framework` (compliance metadata)     |

### Step 5 — Maturity, versioning, tagging

- `Maturity.EXPERIMENTAL` — new, may have bugs / perf issues. Use for testing detection capabilities.
- `Maturity.STABLE` — production-ready, well-tested, optimized.

Versioning follows semver (`0.1.0` initial, `0.2.0` add facts, `0.2.1` bug fix, `1.0.0` production-ready).

Tag categories:

- **Category**: `infrastructure`, `identity`, `data`, `network`, `compute`.
- **Type**: `attack_surface`, `misconfiguration`, `compliance`, `vulnerability`.
- **Provider**: `aws`, `azure`, `gcp`, `github`, `okta`.
- **Threat model**: `stride:spoofing`, `stride:tampering`, `stride:repudiation`, `stride:information_disclosure`, `stride:denial_of_service`, `stride:elevation_of_privilege`.

### Step 6 — Register the Rule

In `cartography/rules/data/rules/__init__.py`:

```python
from cartography.rules.data.rules.my_security_rule import my_security_rule

RULES = {
    # ... existing rules
    my_security_rule.id: my_security_rule,
}
```

### Step 7 — Test it

```bash
cartography-rules list my_security_rule
cartography-rules run my_security_rule
cartography-rules run my_security_rule --output json
cartography-rules run my_security_rule --no-experimental
```

## Compliance frameworks

For CIS, NIST, SOC2, etc., attach a `Framework` object instead of polluting tags:

```python
from cartography.rules.spec.model import Framework

my_rule = Rule(
    id="cis_aws_1_14_access_key_not_rotated",
    name="CIS AWS 1.14: Access Keys Not Rotated",
    # ...
    tags=("iam", "credentials", "stride:spoofing"),  # category tags only
    frameworks=(
        Framework(
            name="CIS AWS Foundations Benchmark",
            short_name="CIS",
            scope="aws",
            revision="5.0",
            requirement="1.14",
        ),
    ),
)
```

Compliance-style tags like `cis:1.14`, `cis:aws-5.0` must NOT live in `tags`. CLI users filter via `--framework CIS`, `--framework CIS:aws`, `--framework CIS:aws:5.0`.

For deeper framework guidance, including CIS benchmark conventions (rule names, IDs, file naming, headers, references), see `references/compliance-frameworks.md` and `references/cis-conventions.md`.

## Cross-provider rules

Group facts from different cloud providers under one rule. Each fact's `cypher_query` should include the provider in the result so the Finding has it:

```python
_aws_unencrypted_storage = Fact(
    id="aws-s3-unencrypted",
    cypher_query="""
    MATCH (b:S3Bucket) WHERE b.default_encryption IS NULL
    RETURN b.id AS id, b.name AS name, 'aws' AS provider
    """,
    # ...
    module=Module.AWS,
    maturity=Maturity.STABLE,
)


_azure_unencrypted_storage = Fact(
    id="azure-storage-unencrypted",
    cypher_query="""
    MATCH (s:AzureStorageAccount) WHERE s.encryption_enabled = false
    RETURN s.id AS id, s.name AS name, 'azure' AS provider
    """,
    module=Module.AZURE,
    maturity=Maturity.STABLE,
)


class UnencryptedStorageOutput(Finding):
    id: str | None = None
    name: str | None = None
    provider: str | None = None


unencrypted_storage = Rule(
    id="unencrypted_storage",
    name="Unencrypted Cloud Storage",
    description="Detects unencrypted storage across cloud providers",
    output_model=UnencryptedStorageOutput,
    tags=("data", "encryption", "compliance"),
    facts=(_aws_unencrypted_storage, _azure_unencrypted_storage),
    version="1.0.0",
)
```

## Using the ontology

Leverage semantic labels (e.g. `UserAccount`) and `_ont_*` properties for cross-module detection:

```python
_unmanaged_accounts = Fact(
    id="unmanaged-accounts-ontology",
    name="User Accounts Not Linked to Identity",
    description="Detects user accounts without a corresponding User identity",
    cypher_query="""
    MATCH (ua:UserAccount)
    WHERE NOT (ua)<-[:HAS_ACCOUNT]-(:User)
    RETURN ua.id AS id, ua._ont_email AS email, ua._ont_source AS source
    """,
    cypher_visual_query="""
    MATCH (ua:UserAccount)
    WHERE NOT (ua)<-[:HAS_ACCOUNT]-(:User)
    RETURN ua
    """,
    cypher_count_query="""
    MATCH (ua:UserAccount)
    RETURN COUNT(ua) AS count
    """,
    module=Module.CROSS_CLOUD,
    maturity=Maturity.STABLE,
)
```

For semantic-label setup, see the `enrich-ontology` skill.

## References (load on demand)

- `references/compliance-frameworks.md` — `Framework` field reference, CLI filtering, `Rule.has_framework()` checks.
- `references/ontology-in-rules.md` — using `UserAccount` / `Tenant` / `Database` labels and `_ont_*` props in rule queries.
- `references/cis-conventions.md` — CIS rule naming, IDs, file layout, headers, references, complete CIS example.

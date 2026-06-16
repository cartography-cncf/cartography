# CIS Benchmark conventions

When creating CIS (Center for Internet Security) compliance rules, follow these additional conventions on top of the standard rule format.

## Contents

- Rule names
- Rule IDs
- File naming
- Comment headers
- Tags vs frameworks
- CIS references
- Complete CIS example

## Rule names

Format: framework-neutral security concept. Do **not** prefix `Rule.name` with `CIS <PROVIDER> <CONTROL_NUMBER>`.

```python
# Correct
name="Access Keys Not Rotated"
name="S3 Bucket Versioning"
name="SSL Policies With Weak Cipher Suites"

# Incorrect - compliance prefix belongs in frameworks metadata
name="CIS AWS 1.14: Access Keys Not Rotated"
```

## Rule IDs

Format: provider/security concept. Do **not** encode the CIS framework or control number in `Rule.id`.

```python
# Correct
id="aws_access_keys_not_rotated"
id="gcp_default_network_exists"
id="google_workspace_users_without_2sv"

# Incorrect
id="cis_aws_1_14_access_key_not_rotated"
```

### Why keep framework identity out of the rule?

Rules are reusable security detections. Compliance controls are one mapping onto a detection, and multiple frameworks may map to the same rule.

Keep the provider in the rule ID when it is part of the detection concept, such as `aws_access_keys_not_rotated` or `gcp_default_network_exists`. Keep the framework, benchmark revision, requirement/control id, and external control title in `frameworks=`.

A compliance UI can render a control-specific label from `{framework label} {requirement}: {framework.control_title}` without changing `Rule.name`.

Many Cartography rules may map to the same external control. Do not prefix rule IDs or rule names with framework/control labels like `CIS AWS 6.5`.

## File naming

Rule files may be grouped by benchmark/provider for maintainability, but individual rule IDs and names stay security-oriented:

```
cis_aws_iam.py        # CIS AWS Section 1 (IAM)
cis_aws_storage.py    # CIS AWS Section 2 (Storage)
cis_aws_logging.py    # CIS AWS Section 3 (Logging)
cis_aws_networking.py # CIS AWS Section 5 (Networking)
cis_gcp_iam.py        # CIS GCP IAM controls
cis_azure_iam.py      # CIS Azure IAM controls
```

## Comment headers

```python
# =============================================================================
# Access keys not rotated in 90 days
# CIS AWS 1.14
# Main node: AccountAccessKey
# =============================================================================
```

For controls that are not covered yet, use the same header style so gaps are easy to spot and grep for:

```python
# =============================================================================
# TODO: Access keys not rotated in 90 days
# CIS AWS 1.14
# Missing: IAM access key rotation detection
# =============================================================================
```

## Tags vs frameworks

Use `frameworks` for compliance refs. Prefer framework helpers so canonical control titles stay centralized:

```python
from cartography.rules.data.frameworks.cis import cis_aws

frameworks=(cis_aws("1.14"),)
```

Each CIS helper encodes the one active benchmark revision Cartography supports for that benchmark scope today. If multiple CIS revisions need to be active at once, add version-aware helpers or explicit `Framework(...)` mappings instead of overloading one helper.

For helpers with known canonical control-title lookups, prefer the helper default. Only pass `control_title=` to a helper when the central lookup is intentionally not correct for that mapping. When overriding a helper title in a rule file, add that file and helper name to `ALLOWED_HELPER_CONTROL_TITLE_OVERRIDES` in `tests/unit/rules/test_rule_identity.py`.

For a framework without a helper or known lookup control title, set `Framework.control_title` directly:

```python
frameworks=(
    Framework(
        name="CIS AWS Foundations Benchmark",
        short_name="CIS",
        scope="aws",
        revision="5.0",
        requirement="1.14",
        control_title="Ensure access keys are rotated every 90 days or less",
    ),
)
```

Use `tags` for categories only:

```python
tags=("iam", "credentials", "stride:spoofing")
```

Do **NOT** mix compliance info into tags:

```python
# Incorrect — compliance info belongs in frameworks
tags=("cis:1.14", "cis:aws-5.0", "iam", "credentials")
```

## CIS references

Always include the official CIS benchmark reference:

```python
CIS_REFERENCES = [
    RuleReference(
        text="CIS AWS Foundations Benchmark v5.0",
        url="https://www.cisecurity.org/benchmark/amazon_web_services",
    ),
]
```

### Official CIS benchmark links

- [CIS AWS Foundations Benchmark](https://www.cisecurity.org/benchmark/amazon_web_services)
- [CIS GCP Foundations Benchmark](https://www.cisecurity.org/benchmark/google_cloud_computing_platform)
- [CIS Azure Foundations Benchmark](https://www.cisecurity.org/benchmark/azure)
- [CIS Kubernetes Benchmark](https://www.cisecurity.org/benchmark/kubernetes)

### Additional resources

- [AWS Security Hub CIS Controls](https://docs.aws.amazon.com/securityhub/latest/userguide/cis-aws-foundations-benchmark.html)

## Complete CIS example

```python
from cartography.rules.spec.model import (
    Fact, Finding, Maturity, Module, Rule, RuleReference,
)
from cartography.rules.data.frameworks.cis import cis_aws


# =============================================================================
# Access keys not rotated in 90 days
# CIS AWS 1.14
# Main node: AccountAccessKey
# =============================================================================

_aws_access_keys_not_rotated = Fact(
    id="aws-access-keys-not-rotated",
    name="Access Keys Not Rotated",
    description="Identifies IAM access keys that have not been rotated in the past 90 days",
    cypher_query="""
    MATCH (key:AccountAccessKey)
    WHERE key.create_date < datetime() - duration('P90D')
    RETURN key.id AS id, key.user_name AS user_name, key.create_date AS create_date
    """,
    cypher_visual_query="""
    MATCH (key:AccountAccessKey)
    WHERE key.create_date < datetime() - duration('P90D')
    RETURN key
    """,
    cypher_count_query="""
    MATCH (key:AccountAccessKey)
    RETURN COUNT(key) AS count
    """,
    identity_fields=("id",),
    module=Module.AWS,
    maturity=Maturity.STABLE,
)


class CIS114Output(Finding):
    user_name: str | None = None    # human-readable label first: used as the finding title
    id: str | None = None
    create_date: str | None = None


aws_access_keys_not_rotated = Rule(
    id="aws_access_keys_not_rotated",
    name="Access Keys Not Rotated",
    description="IAM access keys should be rotated every 90 days or less",
    output_model=CIS114Output,
    tags=("iam", "credentials", "stride:spoofing"),
    facts=(_aws_access_keys_not_rotated,),
    references=[
        RuleReference(
            text="CIS AWS Foundations Benchmark v5.0",
            url="https://www.cisecurity.org/benchmark/amazon_web_services",
        ),
    ],
    frameworks=(
        cis_aws("1.14"),
    ),
    version="1.0.0",
)
```

# Compliance frameworks

Rules can be linked to compliance frameworks (CIS, NIST, SOC2, ...) using the `Framework` dataclass. This provides structured metadata for filtering and reporting.

## The `Framework` object

```python
from cartography.rules.spec.model import Framework

Framework(
    name="CIS AWS Foundations Benchmark",  # full framework name
    short_name="CIS",                       # abbreviated name for filtering
    requirement="1.14",                     # specific requirement identifier
    scope="aws",                            # optional: platform/domain (aws, gcp, googleworkspace)
    revision="5.0",                         # optional: framework version
)
```

Behaviour:

- All fields are **case-insensitive** and normalised to lowercase internally.
- `scope` should match the Cartography module identifier (e.g. `aws`, `gcp`, `googleworkspace`).
- `requirement` is the specific control number from the framework.

## Adding a Framework to a Rule

```python
from cartography.rules.spec.model import Framework, Rule

my_rule = Rule(
    id="cis_aws_1_14_access_key_not_rotated",
    name="CIS AWS 1.14: Access Keys Not Rotated",
    # ... other fields ...
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

Compliance-specific tags like `cis:1.14` and `cis:aws-5.0` must be **removed** from `tags` and replaced with a `Framework`. Keep only category tags (`iam`, `credentials`, `stride:*`) in `tags`.

## CLI filtering

```bash
# all CIS rules
cartography-rules list --framework CIS

# CIS rules for AWS
cartography-rules list --framework CIS:aws

# CIS AWS 5.0 rules specifically
cartography-rules list --framework CIS:aws:5.0

# run all CIS rules
cartography-rules run all --framework CIS

# list available frameworks
cartography-rules frameworks
```

## Checking framework membership in Python

```python
rule.has_framework("CIS")              # any CIS framework
rule.has_framework("CIS", "aws")       # CIS AWS framework
rule.has_framework("CIS", "aws", "5.0")# CIS AWS 5.0 specifically
```

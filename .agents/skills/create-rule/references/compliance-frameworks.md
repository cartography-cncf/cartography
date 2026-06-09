# Compliance frameworks

Rules can be linked to compliance frameworks (CIS, NIST, SOC2, ...) using the `Framework` dataclass. This provides structured metadata for filtering and reporting.

## The `Framework` object

```python
from cartography.rules.spec.model import Framework

Framework(
    name="CIS AWS Foundations Benchmark",  # full framework name
    short_name="CIS",                       # abbreviated name for filtering
    requirement="1.14",                     # specific requirement/control id
    scope="aws",                            # optional: platform/domain (aws, gcp, googleworkspace)
    revision="5.0",                         # optional: framework version
    control_title="Ensure access keys are rotated every 90 days or less",  # optional: external control title
)
```

Behaviour:

- Matching fields are **case-insensitive** and normalised to lowercase internally.
- `scope` should match the Cartography module identifier (e.g. `aws`, `gcp`, `googleworkspace`).
- `requirement` is the specific requirement/control id from the framework, such as `5.1.8`, `8.2`, or `govern 5`.
- `control_title` is user-facing control copy. Preserve display casing and do not use it for matching or filtering.

## Adding a Framework to a Rule

```python
from cartography.rules.data.frameworks.cis import cis_aws
from cartography.rules.spec.model import Rule

my_rule = Rule(
    id="aws_access_keys_not_rotated",
    name="Access Keys Not Rotated",
    # ... other fields ...
    tags=("iam", "credentials", "stride:spoofing"),  # category tags only
    frameworks=(
        cis_aws("1.14"),
    ),
)
```

Compliance-specific tags like `cis:1.14` and `cis:aws-5.0` must be **removed** from `tags` and replaced with a `Framework`. Keep only category tags (`iam`, `credentials`, `stride:*`) in `tags`.

Rule identity stays framework-neutral. A compliance UI can render framework-specific labels from `{framework label} {requirement}: {framework.control_title}` without changing `Rule.name`.

`Rule.name` should describe the security detection in Cartography terms. `Framework.control_title` should describe the external framework control or requirement. Many Cartography rules may map to the same external framework control.

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

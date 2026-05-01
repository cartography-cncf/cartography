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

Format: **`CIS <PROVIDER> <CONTROL_NUMBER>: <Description>`**

```python
# Correct
name="CIS AWS 1.14: Access Keys Not Rotated"
name="CIS AWS 2.1.1: S3 Bucket Versioning"
name="CIS GCP 3.9: SSL Policies With Weak Cipher Suites"

# Incorrect — missing provider
name="CIS 1.14: Access Keys Not Rotated"
```

## Rule IDs

Format: **`cis_<provider>_<control_number>_<short_slug>`**

```python
# Correct
id="cis_aws_1_14_access_key_not_rotated"
id="cis_gcp_3_1_default_network"
id="cis_gw_4_1_1_3_user_2sv_not_enforced"

# Incorrect
id="cis_1_14_access_key_not_rotated"
```

### Why include the provider?

CIS control numbers don't map 1:1 across providers:

- CIS AWS 1.18 (Expired SSL/TLS Certificates) has no GCP equivalent.
- CIS AWS 5.1 vs CIS GCP 3.9 cover different networking concepts despite similar numbers.

Including the provider keeps rule names self-documenting in alerts, dashboards, reports, and SIEM integrations.

## File naming

Organise by provider and benchmark section:

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
# CIS AWS 1.14: Access keys not rotated in 90 days
# Main node: AccountAccessKey
# =============================================================================
```

## Tags vs frameworks

Use `frameworks` for compliance refs:

```python
frameworks=(
    Framework(
        name="CIS AWS Foundations Benchmark",
        short_name="CIS",
        scope="aws",
        revision="5.0",
        requirement="1.14",
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
    Fact, Finding, Framework, Maturity, Module, Rule, RuleReference,
)


# =============================================================================
# CIS AWS 1.14: Access keys not rotated in 90 days
# Main node: AccountAccessKey
# =============================================================================

_cis_aws_1_14_fact = Fact(
    id="cis-aws-1-14-access-key-not-rotated",
    name="CIS AWS 1.14: Access Keys Not Rotated",
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
    module=Module.AWS,
    maturity=Maturity.STABLE,
)


class CIS114Output(Finding):
    id: str | None = None
    user_name: str | None = None
    create_date: str | None = None


cis_aws_1_14_access_key_not_rotated = Rule(
    id="cis_aws_1_14_access_key_not_rotated",
    name="CIS AWS 1.14: Access Keys Not Rotated",
    description="IAM access keys should be rotated every 90 days or less",
    output_model=CIS114Output,
    tags=("iam", "credentials", "stride:spoofing"),
    facts=(_cis_aws_1_14_fact,),
    references=[
        RuleReference(
            text="CIS AWS Foundations Benchmark v5.0",
            url="https://www.cisecurity.org/benchmark/amazon_web_services",
        ),
    ],
    frameworks=(
        Framework(
            name="CIS AWS Foundations Benchmark",
            short_name="CIS",
            scope="aws",
            revision="5.0",
            requirement="1.14",
        ),
    ),
    version="1.0.0",
)
```

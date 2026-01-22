# AGENTS.md: Cartography Rules Development Guide

> **For AI Coding Assistants**: This document provides guidance for developing Cartography security rules, with specific conventions for CIS benchmark compliance rules.

## CIS Benchmark Rules

When adding CIS compliance rules, follow these naming conventions:

### Rule Names

Use the format: **`CIS <PROVIDER> <CONTROL_NUMBER>: <Description>`**

```python
# Correct
name="CIS AWS 1.14: Access Keys Not Rotated"
name="CIS AWS 2.1.1: S3 Bucket Versioning"
name="CIS GCP 3.9: SSL Policies With Weak Cipher Suites"

# Incorrect - missing provider
name="CIS 1.14: Access Keys Not Rotated"
```

### Why Include the Provider?

CIS control numbers don't map 1:1 across cloud providers. For example:

- CIS AWS 1.18 (Expired SSL/TLS Certificates) has no GCP equivalent
- CIS AWS 5.1 vs CIS GCP 3.9 cover different networking concepts despite similar numbers

Including the provider ensures rule names are **self-documenting** when viewed in isolation (alerts, dashboards, reports, SIEM integrations).

### File Naming

Organize by provider and benchmark section:

```
cis_aws_iam.py        # CIS AWS Section 1 (IAM)
cis_aws_storage.py    # CIS AWS Section 2 (Storage)
cis_aws_logging.py    # CIS AWS Section 3 (Logging)
cis_aws_networking.py # CIS AWS Section 5 (Networking)
cis_gcp_iam.py        # CIS GCP IAM controls
cis_azure_iam.py      # CIS Azure IAM controls
```

### Comment Headers

Match the rule name format in section comments:

```python
# =============================================================================
# CIS AWS 1.14: Access keys not rotated in 90 days
# Main node: AccountAccessKey
# =============================================================================
```

### Tags

Include both control number and benchmark version:

```python
tags=(
    "cis:1.14",           # Control number
    "cis:aws-5.0",        # Benchmark version
    "iam",                # Category
    "credentials",        # Specific area
    "stride:spoofing",    # Threat model
)
```

### Rule IDs

Use lowercase with underscores, prefixed with `cis_`:

```python
id="cis_1_14_access_key_not_rotated"
id="cis_2_1_1_s3_versioning"
```

### References

Always include the official CIS benchmark reference:

```python
CIS_REFERENCES = [
    RuleReference(
        text="CIS AWS Foundations Benchmark v5.0",
        url="https://www.cisecurity.org/benchmark/amazon_web_services",
    ),
]
```

## Fact Query Structure

Each Fact requires **three** Cypher queries:

### 1. `cypher_query` - Data Query
Returns specific fields for the output model:
```python
cypher_query="""
MATCH (b:S3Bucket)
WHERE b.anonymous_access = true
RETURN b.id AS id, b.name AS name, b.region AS region
"""
```

### 2. `cypher_visual_query` - Visualization Query
Returns nodes/relationships for Neo4j Browser:
```python
cypher_visual_query="""
MATCH (b:S3Bucket)
WHERE b.anonymous_access = true
RETURN *
"""
```

### 3. `cypher_count_query` - Total Asset Count Query
Returns the **total count of all assets** of the type being evaluated (not just those matching the criteria). This enables compliance ratio calculations:

```python
cypher_count_query="""
MATCH (b:S3Bucket)
RETURN COUNT(b) AS count
"""
```

**Important**: The count query should count ALL assets of the relevant type, regardless of whether they match the Fact criteria. For example:
- If `cypher_query` finds public S3 buckets, `cypher_count_query` counts ALL S3 buckets
- If `cypher_query` finds users without MFA, `cypher_count_query` counts ALL users

This allows calculating ratios like "10 public buckets out of 100 total" or "5 users without MFA out of 50 total".

## Official CIS Benchmark Links

- [CIS AWS Foundations Benchmark](https://www.cisecurity.org/benchmark/amazon_web_services)
- [CIS GCP Foundations Benchmark](https://www.cisecurity.org/benchmark/google_cloud_computing_platform)
- [CIS Azure Foundations Benchmark](https://www.cisecurity.org/benchmark/azure)
- [CIS Kubernetes Benchmark](https://www.cisecurity.org/benchmark/kubernetes)

## Additional Resources

- [AWS Security Hub CIS Controls](https://docs.aws.amazon.com/securityhub/latest/userguide/cis-aws-foundations-benchmark.html)

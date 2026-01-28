# Creating Security Rules

> **Related docs**: [Main AGENTS.md](../../AGENTS.md) | [Enriching the Ontology](enrich-ontology.md)

This guide covers how to create security rules in Cartography to identify attack surfaces, security gaps, and compliance issues across your infrastructure.

## Table of Contents

1. [Overview](#overview) - Introduction to the rules system
2. [Rule Architecture](#rule-architecture) - Rules, Facts, and Findings hierarchy
3. [Essential Imports](#essential-imports) - Required imports
4. [Creating Facts](#creating-facts) - Cypher queries for detection
5. [Creating Output Models](#creating-output-models) - Pydantic models for results
6. [Creating Rules](#creating-rules) - Combining facts into rules
7. [Fact Maturity Levels](#fact-maturity-levels) - EXPERIMENTAL vs STABLE
8. [Rule Versioning](#rule-versioning) - Semantic versioning
9. [Tagging Best Practices](#tagging-best-practices) - Categorization tags
10. [Step-by-Step: Creating a New Rule](#step-by-step-creating-a-new-rule) - Complete walkthrough
11. [Cross-Provider Rules](#cross-provider-rules) - Multi-cloud detection
12. [Using Ontology in Rules](#using-ontology-in-rules) - Leverage semantic labels
13. [CIS Benchmark Rules Conventions](#cis-benchmark-rules-conventions) - Compliance rules

## Overview

Cartography includes a powerful rules system that allows you to write security queries using Cypher. Rules can detect issues across multiple cloud providers by combining facts from different modules or leveraging the ontology system.

## Rule Architecture

Rules use a simple two-level hierarchy:

```
Rule (e.g., "database-exposed")
  ├─ Fact (e.g., "aws-rds-public")
  ├─ Fact (e.g., "azure-sql-public")
  └─ Fact (e.g., "gcp-cloudsql-public")
```

- **Rule**: Represents a security issue or attack surface (e.g., "Publicly accessible databases")
- **Fact**: Individual Cypher query that gathers evidence about your environment
- **Finding**: Pydantic model that defines the structure of results

## Essential Imports

```python
from cartography.rules.spec.model import (
    Fact,
    Finding,
    Maturity,
    Module,
    Rule,
    RuleReference,
)
```

## Creating Facts

A Fact is a Cypher query that detects a specific condition in your graph:

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
    module=Module.AWS,
    maturity=Maturity.STABLE,
)
```

### Fact Fields

| Field | Required | Description |
|-------|----------|-------------|
| `id` | Yes | Unique identifier (lowercase, hyphens) |
| `name` | Yes | Human-readable name |
| `description` | Yes | Detailed description of what this fact detects |
| `cypher_query` | Yes | Query returning structured data (must use aliases) |
| `cypher_visual_query` | Yes | Query returning nodes for visualization |
| `module` | Yes | Module enum (AWS, AZURE, GCP, GITHUB, etc.) |
| `maturity` | Yes | EXPERIMENTAL or STABLE |

### Cypher Query Guidelines

**cypher_query** - Returns structured data for processing:
- Must use `AS` aliases that match your Finding model fields
- Should return relevant identifying information
- Keep queries efficient - avoid expensive operations

```python
cypher_query="""
MATCH (resource:SomeNode)
WHERE resource.vulnerable = true
RETURN resource.id AS id,
       resource.name AS name,
       resource.region AS region,
       resource.severity AS severity
"""
```

**cypher_visual_query** - Returns nodes for graph visualization:
- Returns the actual nodes (not just properties)
- Used by UI tools to display affected resources

```python
cypher_visual_query="""
MATCH (resource:SomeNode)
WHERE resource.vulnerable = true
RETURN resource
"""
```

## Creating Output Models

Each Rule must define an output model that extends `Finding`:

```python
from cartography.rules.spec.model import Finding

class DatabaseExposedOutput(Finding):
    """Output model for publicly exposed databases."""

    # Fields must match cypher_query aliases
    id: str | None = None
    name: str | None = None
    region: str | None = None
```

**Key Points:**
- **Inherit from `Finding`**: Your model must extend the base class
- **Match Query Aliases**: Field names must match `cypher_query` `AS` aliases exactly
- **Use Optional Types**: All fields should be `| None` with default `None`
- **Automatic Fields**: The `source` field is auto-populated with the module name

## Creating Rules

Combine one or more facts into a rule:

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

### Rule Fields

| Field | Required | Description |
|-------|----------|-------------|
| `id` | Yes | Unique identifier (lowercase, underscores) |
| `name` | Yes | Human-readable name |
| `description` | Yes | What security issue this rule detects |
| `output_model` | Yes | Pydantic model class for results |
| `tags` | Yes | Tuple of categorization tags |
| `facts` | Yes | Tuple of Fact objects |
| `version` | Yes | Semantic version string |
| `references` | No | List of RuleReference for documentation |

### Adding References

Include references to external documentation:

```python
from cartography.rules.spec.model import RuleReference

my_rule = Rule(
    id="my-rule",
    # ... other fields ...
    references=[
        RuleReference(
            text="AWS Security Best Practices",
            url="https://docs.aws.amazon.com/security/",
        ),
        RuleReference(
            text="OWASP Cloud Security",
            url="https://owasp.org/www-project-cloud-security/",
        ),
    ],
)
```

## Fact Maturity Levels

### EXPERIMENTAL
- New facts, recently added
- May have bugs or performance issues
- Limited production testing
- Use for testing new detection capabilities

```python
maturity=Maturity.EXPERIMENTAL
```

### STABLE
- Production-ready, well-tested
- Optimized queries, consistent results
- Use for production monitoring and compliance

```python
maturity=Maturity.STABLE
```

## Rule Versioning

Use semantic versioning:

```python
version="0.1.0"  # Initial release
version="0.2.0"  # Added new facts (minor)
version="0.2.1"  # Bug fix (patch)
version="1.0.0"  # Production ready (major)
```

## Tagging Best Practices

Use consistent tags for categorization:

```python
tags=(
    "infrastructure",      # Category: infrastructure, identity, data, network
    "attack_surface",      # Type: attack_surface, misconfiguration, compliance
    "database",            # Specific area
    "stride:tampering",    # Optional: STRIDE threat model
)
```

**Common tag categories:**
- **Category**: `infrastructure`, `identity`, `data`, `network`, `compute`
- **Type**: `attack_surface`, `misconfiguration`, `compliance`, `vulnerability`
- **Provider**: `aws`, `azure`, `gcp`, `github`, `okta`
- **Threat model**: `stride:spoofing`, `stride:tampering`, `stride:repudiation`, `stride:information_disclosure`, `stride:denial_of_service`, `stride:elevation_of_privilege`

## Step-by-Step: Creating a New Rule

### 1. Create the Rule File

Create a new file in `cartography/rules/data/rules/`:

```python
# cartography/rules/data/rules/my_security_rule.py
from cartography.rules.spec.model import Fact, Finding, Maturity, Module, Rule

# =============================================================================
# My Security Rule: Detect vulnerable configuration
# Main node: SomeResource
# =============================================================================

_my_fact = Fact(
    id="my-fact-id",
    name="My Fact Name",
    description="Detailed description of what this detects",
    cypher_query="""
    MATCH (r:SomeResource)
    WHERE r.vulnerable = true
    RETURN r.id AS id, r.name AS name
    """,
    cypher_visual_query="""
    MATCH (r:SomeResource)
    WHERE r.vulnerable = true
    RETURN r
    """,
    module=Module.AWS,
    maturity=Maturity.EXPERIMENTAL,
)


class MyRuleOutput(Finding):
    id: str | None = None
    name: str | None = None


my_security_rule = Rule(
    id="my_security_rule",
    name="My Security Rule",
    description="Detects vulnerable configurations",
    output_model=MyRuleOutput,
    tags=("security", "misconfiguration"),
    facts=(_my_fact,),
    version="0.1.0",
)
```

### 2. Register the Rule

Add to `cartography/rules/data/rules/__init__.py`:

```python
from cartography.rules.data.rules.my_security_rule import my_security_rule

RULES = {
    # ... existing rules
    my_security_rule.id: my_security_rule,
}
```

### 3. Test the Rule

```bash
# List rule details
cartography-rules list my_security_rule

# Run the rule
cartography-rules run my_security_rule

# Run with JSON output
cartography-rules run my_security_rule --output json

# Exclude experimental facts
cartography-rules run my_security_rule --no-experimental
```

## Cross-Provider Rules

Create rules that span multiple cloud providers:

```python
# AWS fact
_aws_unencrypted_storage = Fact(
    id="aws-s3-unencrypted",
    name="Unencrypted AWS S3 Buckets",
    cypher_query="""
    MATCH (b:S3Bucket)
    WHERE b.default_encryption IS NULL
    RETURN b.id AS id, b.name AS name, 'aws' AS provider
    """,
    # ...
    module=Module.AWS,
    maturity=Maturity.STABLE,
)

# Azure fact
_azure_unencrypted_storage = Fact(
    id="azure-storage-unencrypted",
    name="Unencrypted Azure Storage Accounts",
    cypher_query="""
    MATCH (s:AzureStorageAccount)
    WHERE s.encryption_enabled = false
    RETURN s.id AS id, s.name AS name, 'azure' AS provider
    """,
    # ...
    module=Module.AZURE,
    maturity=Maturity.STABLE,
)

# Combined rule
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

## Using Ontology in Rules

Leverage the ontology system for cross-module detection:

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
    module=Module.ONTOLOGY,
    maturity=Maturity.STABLE,
)
```

---

## CIS Benchmark Rules Conventions

When creating CIS (Center for Internet Security) compliance rules, follow these additional conventions:

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

```python
# =============================================================================
# CIS AWS 1.14: Access keys not rotated in 90 days
# Main node: AccountAccessKey
# =============================================================================
```

### Tags

Include control number and benchmark version:

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

### CIS References

Always include the official CIS benchmark reference:

```python
CIS_REFERENCES = [
    RuleReference(
        text="CIS AWS Foundations Benchmark v5.0",
        url="https://www.cisecurity.org/benchmark/amazon_web_services",
    ),
]
```

### Official CIS Benchmark Links

- [CIS AWS Foundations Benchmark](https://www.cisecurity.org/benchmark/amazon_web_services)
- [CIS GCP Foundations Benchmark](https://www.cisecurity.org/benchmark/google_cloud_computing_platform)
- [CIS Azure Foundations Benchmark](https://www.cisecurity.org/benchmark/azure)
- [CIS Kubernetes Benchmark](https://www.cisecurity.org/benchmark/kubernetes)

### Additional Resources

- [AWS Security Hub CIS Controls](https://docs.aws.amazon.com/securityhub/latest/userguide/cis-aws-foundations-benchmark.html)

### Complete CIS Example

```python
from cartography.rules.spec.model import Fact, Finding, Maturity, Module, Rule, RuleReference

# =============================================================================
# CIS AWS 1.14: Access keys not rotated in 90 days
# Main node: AccountAccessKey
# =============================================================================

_cis_1_14_fact = Fact(
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
    module=Module.AWS,
    maturity=Maturity.STABLE,
)


class CIS114Output(Finding):
    id: str | None = None
    user_name: str | None = None
    create_date: str | None = None


cis_1_14_access_key_not_rotated = Rule(
    id="cis_1_14_access_key_not_rotated",
    name="CIS AWS 1.14: Access Keys Not Rotated",
    description="IAM access keys should be rotated every 90 days or less",
    output_model=CIS114Output,
    tags=(
        "cis:1.14",
        "cis:aws-5.0",
        "iam",
        "credentials",
        "stride:spoofing",
    ),
    facts=(_cis_1_14_fact,),
    references=[
        RuleReference(
            text="CIS AWS Foundations Benchmark v5.0",
            url="https://www.cisecurity.org/benchmark/amazon_web_services",
        ),
    ],
    version="1.0.0",
)
```

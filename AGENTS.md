# AGENTS.md: Cartography Intel Module Development Guide

> **For AI Coding Assistants**: This document provides comprehensive guidance for understanding and developing Cartography intel modules. It contains codebase-specific patterns, architectural decisions, and implementation details necessary for effective AI-assisted development within the Cartography project.

This guide teaches you how to write intel modules for Cartography using the modern data model approach. We'll walk through real examples from the codebase to show you the patterns and best practices.

## Procedure Documentation

Detailed procedures are available in separate documents:

| Procedure | Description |
|-----------|-------------|
| [Creating a New Module](docs/agents/create-module.md) | Complete guide to creating a new Cartography intel module |
| [Enriching the Ontology](docs/agents/enrich-ontology.md) | Adding ontology mappings for cross-module querying |
| [Adding a New Node Type](docs/agents/add-node-type.md) | Advanced node schema properties and configurations |
| [Adding a New Relationship](docs/agents/add-relationship.md) | Relationships, MatchLinks, and multi-module patterns |
| [Creating Security Rules](docs/agents/create-rule.md) | Security rules, facts, and compliance conventions |
| [Refactoring Legacy Code](docs/agents/refactor-legacy.md) | Converting legacy Cypher to modern data model |

## AI Assistant Quick Reference

**Key Cartography Concepts:**
- **Intel Module**: Component that fetches data from external APIs and loads into Neo4j
- **Sync Pattern**: `get()` -> `transform()` -> `load()` -> `cleanup()`
- **Data Model**: Declarative schema using `CartographyNodeSchema` and `CartographyRelSchema`
- **Update Tag**: Timestamp used for cleanup jobs to remove stale data

**Critical Files to Know:**
- `cartography/config.py` - Configuration object definitions
- `cartography/cli.py` - Command-line argument definitions
- `cartography/client/core/tx.py` - Core `load()` function
- `cartography/graph/job.py` - Cleanup job utilities
- `cartography/models/core/` - Base data model classes

**Essential Imports:**
```python
from dataclasses import dataclass
from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties, CartographyNodeSchema, ExtraNodeLabels
from cartography.models.core.relationships import (
    CartographyRelProperties, CartographyRelSchema, LinkDirection,
    make_target_node_matcher, TargetNodeMatcher, OtherRelationships,
)
from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.util import timeit
```

**PropertyRef Quick Reference:**
```python
PropertyRef("field_name")                          # Value from data dict
PropertyRef("KWARG_NAME", set_in_kwargs=True)      # Value from load() kwargs
PropertyRef("field", extra_index=True)             # Create database index
PropertyRef("field_list", one_to_many=True)        # One-to-many relationships
```

**Debugging Tips:**
- Check existing patterns in `cartography/intel/` before creating new ones
- Ensure `__init__.py` files exist in all module directories
- Look at `tests/integration/cartography/intel/` for similar test patterns
- Review `cartography/models/` for existing relationship patterns

## Git and Pull Request Guidelines

**Signing Commits**: All commits must be signed using the `-s` flag. This adds a `Signed-off-by` line to your commit message, certifying that you have the right to submit the code under the project's license.

```bash
# Sign a commit with a message
git commit -s -m "feat(module): add new feature"
```

**Pull Request Descriptions**: When creating a pull request, use the template at `.github/pull_request_template.md`.

Example PR creation:
```bash
gh pr create --title "feat(core): add BufferError retry handling" --body "$(cat <<'EOF'
### Summary
Add retry handling for BufferError to cartography's core Neo4j retry logic.

### Related issues or links
- https://github.com/cartography-cncf/cartography/issues/1234

### Checklist
- [x] Update/add unit or integration tests.
EOF
)"
```

## Quick Start: Copy an Existing Module

The fastest way to get started is to copy the structure from an existing module:

- **Simple module**: `cartography/intel/lastpass/` - Basic user sync with API calls
- **Complex module**: `cartography/intel/aws/ec2/instances.py` - Multiple relationships and data types
- **Reference documentation**: `docs/root/dev/writing-intel-modules.md`

## Module Structure Overview

Every Cartography intel module follows this structure:

```
cartography/intel/your_module/
├── __init__.py          # Main entry point with sync orchestration
├── users.py             # Domain-specific sync modules (users, devices, etc.)
├── devices.py           # Additional domain modules as needed
└── ...

cartography/models/your_module/
├── user.py              # Data model definitions
├── tenant.py            # Tenant/account model
└── ...
```

### Main Entry Point (`__init__.py`)

```python
import logging
import neo4j
from cartography.config import Config
from cartography.util import timeit
import cartography.intel.your_module.users


logger = logging.getLogger(__name__)


@timeit
def start_your_module_ingestion(neo4j_session: neo4j.Session, config: Config) -> None:
    """
    Main entry point for your module ingestion
    """
    # Validate configuration
    if not config.your_module_api_key:
        logger.info("Your module import is not configured - skipping this module.")
        return

    # Set up common job parameters for cleanup
    common_job_parameters = {
        "UPDATE_TAG": config.update_tag,
        "TENANT_ID": config.your_module_tenant_id,  # if applicable
    }

    # Call domain-specific sync functions
    cartography.intel.your_module.users.sync(
        neo4j_session,
        config.your_module_api_key,
        config.your_module_tenant_id,
        config.update_tag,
        common_job_parameters,
    )
```

## The Sync Pattern: Get, Transform, Load, Cleanup

Every sync function follows this exact pattern:

```python
@timeit
def sync(
    neo4j_session: neo4j.Session,
    api_key: str,
    tenant_id: str,
    update_tag: int,
    common_job_parameters: dict[str, Any],
) -> None:
    """
    Sync function following the standard pattern
    """
    # 1. GET - Fetch data from API
    raw_data = get(api_key, tenant_id)

    # 2. TRANSFORM - Shape data for ingestion
    transformed_data = transform(raw_data)

    # 3. LOAD - Ingest to Neo4j using data model
    load_users(neo4j_session, transformed_data, tenant_id, update_tag)

    # 4. CLEANUP - Remove stale data
    cleanup(neo4j_session, common_job_parameters)
```

For detailed implementation of each step, see [Creating a New Module](docs/agents/create-module.md).

## Data Model Overview

Modern Cartography uses a declarative data model:

```python
from dataclasses import dataclass
from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties, CartographyNodeSchema

@dataclass(frozen=True)
class YourServiceUserNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    email: PropertyRef = PropertyRef("email", extra_index=True)
    name: PropertyRef = PropertyRef("name")

@dataclass(frozen=True)
class YourServiceUserSchema(CartographyNodeSchema):
    label: str = "YourServiceUser"
    properties: YourServiceUserNodeProperties = YourServiceUserNodeProperties()
    sub_resource_relationship: YourServiceTenantToUserRel = YourServiceTenantToUserRel()
```

For detailed schema definitions, see:
- [Adding a New Node Type](docs/agents/add-node-type.md)
- [Adding a New Relationship](docs/agents/add-relationship.md)

## Error Handling Principles

### Fail Loudly When Assumptions Break

Cartography likes to fail loudly so that broken assumptions bubble exceptions up to operators instead of being papered over.

- When key assumptions your code relies upon stop being true, **stop execution immediately** and let the error propagate.
- Lean toward propagating errors up to callers instead of logging a warning inside a `try`/`except` block and continuing.
- If you're confident data should always exist, access it directly. Allow natural `KeyError`, `AttributeError`, or `IndexError` exceptions to signal corruption.
- Never manufacture "safe" default return values for required data.
- Avoid `hasattr()`/`getattr()` for required fields - rely on schemas and tests to detect breakage.

```python
# DON'T: Catch base exceptions and continue silently
try:
    risky_operation()
except Exception:
    logger.error("Something went wrong")
    pass  # Silently continue - BAD!

# DO: Let errors propagate or handle specifically
result = risky_operation()  # Let it fail if something is wrong
```

### Required vs Optional Field Access

```python
def transform_user(user_data: dict[str, Any]) -> dict[str, Any]:
    return {
        # Required field - let it raise KeyError if missing
        "id": user_data["id"],
        "email": user_data["email"],

        # Optional field - gracefully handle missing data
        "name": user_data.get("display_name"),
        "phone": user_data.get("phone_number"),
    }
```

## Configuration and Credentials

### Adding CLI Arguments

Add your configuration options in `cartography/cli.py`:

```python
parser.add_argument(
    '--your-service-api-key-env-var',
    type=str,
    help='Name of environment variable containing Your Service API key',
)
```

### Configuration Object

Add fields to `cartography/config.py`:

```python
@dataclass
class Config:
    your_service_api_key: str | None = None
    your_service_tenant_id: str | None = None
```

### Validation in Module

```python
def start_your_service_ingestion(neo4j_session: neo4j.Session, config: Config) -> None:
    if not config.your_service_api_key:
        logger.info("Your Service API key not configured - skipping module")
        return

    api_key = os.getenv(config.your_service_api_key)
    if not api_key:
        logger.error(f"Environment variable {config.your_service_api_key} not set")
        return
```

## Testing Your Module

**Key Principle: Test outcomes, not implementation details.**

```python
from unittest.mock import patch
import cartography.intel.your_service.users
from tests.data.your_service.users import MOCK_USERS_RESPONSE
from tests.integration.util import check_nodes, check_rels

@patch.object(cartography.intel.your_service.users, "get", return_value=MOCK_USERS_RESPONSE)
def test_sync_users(mock_api, neo4j_session):
    cartography.intel.your_service.users.sync(
        neo4j_session,
        "fake-api-key",
        TEST_TENANT_ID,
        TEST_UPDATE_TAG,
        {"UPDATE_TAG": TEST_UPDATE_TAG, "TENANT_ID": TEST_TENANT_ID},
    )

    # Test outcomes - verify data is written to the graph as expected
    expected_nodes = {("user-123", "alice@example.com")}
    assert check_nodes(neo4j_session, "YourServiceUser", ["id", "email"]) == expected_nodes
```

For detailed testing guidance, see [Creating a New Module](docs/agents/create-module.md#testing-your-module).

## Final Checklist

Before submitting your module:

- [ ] **Configuration**: CLI args, config validation, credential handling
- [ ] **Sync Pattern**: get() -> transform() -> load() -> cleanup()
- [ ] **Data Model**: Node properties, relationships, proper typing
- [ ] **Schema Fields**: Only use standard fields in `CartographyRelSchema`/`CartographyNodeSchema` subclasses
- [ ] **Scoped Cleanup**: Verify `scoped_cleanup=True` (default) for tenant-scoped resources, `False` only for global data
- [ ] **Error Handling**: Specific exceptions, required vs optional fields
- [ ] **Testing**: Integration tests for sync functions
- [ ] **Documentation**: Schema docs, docstrings, inline comments
- [ ] **Cleanup**: Proper cleanup job implementation
- [ ] **Indexing**: Extra indexes on frequently queried fields

## Type Hints Style Guide

Use Python 3.9+ style type hints:

```python
# DO: Use built-in type hints (Python 3.9+)
def get_users(api_key: str) -> dict[str, Any]:
    ...

# DO: Use union operator for optional types
def process_user(user_id: str | None) -> None:
    ...

# DON'T: Use objects from typing module (Dict, List, Optional)
```

---

Remember: Start simple, iterate, and use existing modules as references. The Cartography community is here to help!

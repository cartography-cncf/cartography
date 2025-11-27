# Guide: Adding a New Integration to Cartography

This guide documents the step-by-step process for adding a new integration module to Cartography, based on the Kong Konnect integration implementation.

## Quick Reference

### Files to Modify (3)
1. `cartography/config.py` - Add configuration parameters
2. `cartography/cli.py` - Add CLI arguments and parsing
3. `cartography/sync.py` - Register the module

### Folders to Create (2)
1. `cartography/models/yourservice/` - Data model definitions
2. `cartography/intel/yourservice/` - Intelligence/sync modules

---

## Step-by-Step Process

### Step 1: Planning

**Research the API:**
- Obtain API documentation (OpenAPI spec if available)
- Identify authentication method (API key, OAuth, etc.)
- List resources to sync
- Understand pagination patterns
- Note rate limits

**Design the data model:**
- Map API resources to Neo4j node types
- Define relationships between nodes
- Identify required vs optional properties
- Plan the graph hierarchy

**Example (Kong Konnect):**
```
Organization (root)
  ├─ Control Plane
  │   ├─ Service
  │   │   └─ Route (ROUTES_TO relationship)
  │   ├─ DP Node
  │   └─ Certificate
```

---

### Step 2: Add Configuration

#### File: `cartography/config.py`

Add configuration parameters to the `Config` class:

```python
# YourService configuration
yourservice_api_token: Optional[str] = None
yourservice_api_url: Optional[str] = None
yourservice_org_id: Optional[str] = None  # if applicable
```

#### File: `cartography/cli.py`

**Location 1:** In `add_intel_arguments()` function (alphabetically):

```python
parser.add_argument(
    "--yourservice-api-token-env-var",
    type=str,
    default="YOURSERVICE_API_TOKEN",
    help=(
        "The name of an environment variable containing the API token. "
        "Required if you are using the YourService intel module."
    ),
)
parser.add_argument(
    "--yourservice-api-url",
    type=str,
    default="https://api.yourservice.com/v1",
    help="The base URL for the API.",
)
```

**Location 2:** In `main()` method, config parsing section:

```python
# YourService config
if config.yourservice_api_token_env_var:
    logger.debug(
        f"Reading API token from {config.yourservice_api_token_env_var}",
    )
    config.yourservice_api_token = os.environ.get(
        config.yourservice_api_token_env_var
    )
else:
    config.yourservice_api_token = None
```

---

### Step 3: Create Data Models

#### Create directory structure:

```bash
mkdir -p cartography/models/yourservice
touch cartography/models/yourservice/__init__.py
```

#### Node Schema Template

File: `cartography/models/yourservice/resource.py`

```python
from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.relationships import CartographyRelProperties
from cartography.models.core.relationships import CartographyRelSchema
from cartography.models.core.relationships import LinkDirection
from cartography.models.core.relationships import make_target_node_matcher
from cartography.models.core.relationships import OtherRelationships
from cartography.models.core.relationships import TargetNodeMatcher


@dataclass(frozen=True)
class YourResourceNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef('id')
    lastupdated: PropertyRef = PropertyRef('lastupdated', set_in_kwargs=True)
    name: PropertyRef = PropertyRef('name')
    description: PropertyRef = PropertyRef('description')
    created_at: PropertyRef = PropertyRef('created_at')


@dataclass(frozen=True)
class YourResourceToParentRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef('lastupdated', set_in_kwargs=True)


@dataclass(frozen=True)
class YourResourceToParentRel(CartographyRelSchema):
    target_node_label: str = 'ParentNodeLabel'
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {'id': PropertyRef('PARENT_ID', set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "RESOURCE"
    properties: YourResourceToParentRelProperties = YourResourceToParentRelProperties()


@dataclass(frozen=True)
class YourResourceSchema(CartographyNodeSchema):
    label: str = 'YourServiceResource'
    properties: YourResourceNodeProperties = YourResourceNodeProperties()
    other_relationships: OtherRelationships = OtherRelationships(
        [
            YourResourceToParentRel(),
        ],
    )
```

**Key Points:**
- Only `id` and `lastupdated` use `set_in_kwargs=True`
- All other fields are optional (no `set_in_kwargs`)
- Use `other_relationships` for child nodes
- Use `sub_resource_relationship` for root nodes

---

### Step 4: Create Intel Modules

#### Create directory structure:

```bash
mkdir -p cartography/intel/yourservice
touch cartography/intel/yourservice/__init__.py
```

#### Intel Module Template

File: `cartography/intel/yourservice/resource.py`

```python
import logging
from typing import Any, Dict, List

import neo4j
from requests import Session

from cartography.client.core.tx import load
from cartography.models.yourservice.resource import YourResourceSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)
_TIMEOUT = (60, 60)


def get(api_token: str, api_url: str, parent_id: str = None) -> List[Dict[str, Any]]:
    """Fetch resources from the API with pagination."""
    resources = []
    url = f"{api_url}/resources"
    headers = {
        "Authorization": f"Bearer {api_token}",
        "Content-Type": "application/json",
    }

    session = Session()
    offset = None

    logger.info(f"Fetching resources from {url}")

    while True:
        params = {"size": 100}
        if offset:
            params["offset"] = offset

        response = session.get(url, headers=headers, params=params, timeout=_TIMEOUT)
        response.raise_for_status()
        data = response.json()

        resources.extend(data.get("data", []))

        next_offset = data.get("offset")
        if next_offset:
            offset = next_offset
        else:
            break

    logger.info(f"Fetched {len(resources)} resources")
    return resources


def transform(resources_data: List[Dict[str, Any]], parent_id: str = None) -> List[Dict[str, Any]]:
    """Transform API data to match the schema."""
    import json
    
    for resource in resources_data:
        if parent_id:
            resource['parent_id'] = parent_id
        
        # Convert arrays/objects to JSON strings
        if 'tags' in resource and resource['tags']:
            resource['tags'] = json.dumps(resource['tags'])
    
    return resources_data


def load_resources(
    neo4j_session: neo4j.Session,
    data: List[Dict[str, Any]],
    parent_id: str,
    update_tag: int,
) -> None:
    """Load resources into Neo4j."""
    load(
        neo4j_session,
        YourResourceSchema(),
        data,
        lastupdated=update_tag,
        PARENT_ID=parent_id,
    )


def cleanup(neo4j_session: neo4j.Session, common_job_parameters: Dict[str, Any]) -> None:
    """Remove stale resources."""
    query = """
    MATCH (r:YourServiceResource)
    WHERE r.lastupdated <> $UPDATE_TAG
    DETACH DELETE r
    """
    neo4j_session.run(query, UPDATE_TAG=common_job_parameters['UPDATE_TAG'])


@timeit
def sync(
    neo4j_session: neo4j.Session,
    api_token: str,
    api_url: str,
    update_tag: int,
    common_job_parameters: Dict[str, Any],
) -> None:
    """Sync resources."""
    resources_data = get(api_token, api_url)
    transformed_data = transform(resources_data)
    load_resources(neo4j_session, transformed_data, None, update_tag)
    cleanup(neo4j_session, common_job_parameters)
```

#### Main Entry Point

File: `cartography/intel/yourservice/__init__.py`

```python
import logging

import neo4j

from cartography.config import Config
from cartography.intel.yourservice import resource1
from cartography.intel.yourservice import resource2
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def start_yourservice_ingestion(neo4j_session: neo4j.Session, config: Config) -> None:
    """Start YourService ingestion."""
    if not config.yourservice_api_token:
        logger.info(
            "YourService import is not configured - skipping this module. "
            "To enable, set YOURSERVICE_API_TOKEN environment variable.",
        )
        return

    api_url = config.yourservice_api_url or "https://api.yourservice.com/v1"
    
    common_job_parameters = {
        "UPDATE_TAG": config.update_tag,
    }

    # Sync in dependency order (parents before children)
    resource1.sync(
        neo4j_session,
        config.yourservice_api_token,
        api_url,
        config.update_tag,
        common_job_parameters,
    )

    resource2.sync(
        neo4j_session,
        config.yourservice_api_token,
        api_url,
        config.update_tag,
        common_job_parameters,
    )
```

---

### Step 5: Register the Module

#### File: `cartography/sync.py`

**Add import (alphabetically):**
```python
import cartography.intel.yourservice
```

**Add to TOP_LEVEL_MODULES (alphabetically):**
```python
TOP_LEVEL_MODULES: OrderedDict[str, Callable[..., None]] = OrderedDict(
    {
        # ... other modules ...
        "yourservice": cartography.intel.yourservice.start_yourservice_ingestion,
        # ... other modules ...
    }
)
```

---

### Step 6: Testing

#### Test module import:
```bash
python3 -c "import cartography.intel.yourservice; import cartography.models.yourservice"
```

#### Test with real data:
```bash
export YOURSERVICE_API_TOKEN="your-token"
python3 -m cartography --neo4j-uri bolt://localhost:7687 --selected-modules yourservice -v
```

#### Verify in Neo4j:
```python
import neo4j

driver = neo4j.GraphDatabase.driver('bolt://localhost:7687')
with driver.session() as session:
    result = session.run('MATCH (n:YourServiceResource) RETURN count(n) as count')
    count = result.single()['count']
    print(f'Resources synced: {count}')
```

---

## Common Patterns

### Pagination

**Offset-based:**
```python
offset = None
while True:
    params = {"size": 100, "offset": offset}
    data = response.json()
    resources.extend(data["data"])
    offset = data.get("offset")
    if not offset:
        break
```

**Page-based:**
```python
page = 1
while True:
    params = {"page": page, "per_page": 100}
    data = response.json()
    resources.extend(data["items"])
    if page >= data["total_pages"]:
        break
    page += 1
```

### Hierarchical Resources

```python
def get_parent_ids(neo4j_session: neo4j.Session) -> List[str]:
    query = "MATCH (p:ParentResource) RETURN p.id as id"
    results = neo4j_session.run(query)
    return [record['id'] for record in results]

# Sync children for each parent
parent_ids = get_parent_ids(neo4j_session)
for parent_id in parent_ids:
    children = get(api_token, api_url, parent_id)
    transformed = transform(children, parent_id)
    load_children(neo4j_session, transformed, parent_id, update_tag)
```

---

## Checklist

### Setup
- [ ] Create `cartography/models/yourservice/` folder
- [ ] Create `cartography/intel/yourservice/` folder
- [ ] Create `__init__.py` in both folders

### Configuration
- [ ] Add config params to `cartography/config.py`
- [ ] Add CLI arguments to `cartography/cli.py`
- [ ] Add config parsing to `cartography/cli.py`

### Implementation
- [ ] Create data models for each resource
- [ ] Create intel modules for each resource
- [ ] Implement get/transform/load/cleanup pattern

### Registration
- [ ] Import module in `cartography/sync.py`
- [ ] Add to `TOP_LEVEL_MODULES` in `cartography/sync.py`

### Testing
- [ ] Test module import
- [ ] Test sync with real data
- [ ] Verify data in Neo4j
- [ ] Run linter

---

## Kong Konnect Example

**Files Modified:** 3
- `cartography/config.py`
- `cartography/cli.py`
- `cartography/sync.py`

**Files Created:** 15
- 7 data models in `cartography/models/konnect/`
- 7 intel modules in `cartography/intel/konnect/`
- 1 main entry point

**Resources Synced:**
- Organizations, Control Planes, Services, Routes, DP Nodes, Certificates

**Development Time:** ~4-6 hours

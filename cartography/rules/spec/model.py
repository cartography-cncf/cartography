from dataclasses import dataclass
from enum import Enum
from typing import Any


class Module(str, Enum):
    """Services that can be monitored"""

    AWS = "AWS"
    """Amazon Web Services"""

    AZURE = "Azure"
    """Microsoft Azure"""

    GCP = "GCP"
    """Google Cloud Platform"""

    GITHUB = "GitHub"
    """GitHub source code management"""

    OKTA = "Okta"
    """Okta identity and access management"""

    CROSS_CLOUD = "CROSS_CLOUD"
    """Multi-cloud or provider-agnostic rules"""


@dataclass(frozen=True)
class Fact:
    """A Fact gathers information about the environment using a Cypher query."""

    id: str
    """A descriptive identifier for the Fact. Should be globally unique within Cartography."""
    name: str
    """A descriptive name for the Fact."""
    description: str
    """More details about the Fact. Information on details that we're querying for."""
    module: Module
    """The Module that the Fact is associated with e.g. AWS, Azure, GCP, etc."""
    # TODO can we lint the queries. full-on integ tests here are overkill though.
    cypher_query: str
    """The Cypher query to gather information about the environment. Returns data field by field e.g. `RETURN node.prop1, node.prop2`."""
    cypher_visual_query: str
    """
    Same as `cypher_query`, returns it in a visual format for the web interface with `.. RETURN *`.
    Often includes additional relationships to help give context.
    """


@dataclass(frozen=True)
class Requirement:
    """
    A requirement within a security framework with one or more facts.

    Notes:
    - `attributes` is reserved for metadata such as tags, categories, or references.
    - Do NOT put evaluation logic, thresholds, or org-specific preferences here.
    """

    id: str
    name: str
    description: str
    facts: tuple[Fact, ...]
    attributes: dict[str, Any] | None = None
    """
    Metadata attributes for the requirement. Example:
    ```json
    {
        "tactic": "initial_access",
        "technique_id": "T1190",
        "services": ["ec2", "s3", "rds", "azure_storage"],
        "providers": ["AWS", "AZURE"],
    }
    ```
    """
    requirement_url: str | None = None


@dataclass(frozen=True)
class Framework:
    """A security framework containing requirements for comprehensive assessment."""

    id: str
    name: str
    description: str
    version: str
    requirements: tuple[Requirement, ...]
    source_url: str | None = None

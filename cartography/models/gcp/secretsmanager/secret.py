from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.relationships import CartographyRelProperties
from cartography.models.core.relationships import CartographyRelSchema
from cartography.models.core.relationships import LinkDirection
from cartography.models.core.relationships import make_target_node_matcher
from cartography.models.core.relationships import TargetNodeMatcher


@dataclass(frozen=True)
class GCPSecretManagerSecretNodeProperties(CartographyNodeProperties):
    """
    Properties for GCP Secret Manager Secret
    """

    id: PropertyRef = PropertyRef("id")
    name: PropertyRef = PropertyRef("name", extra_index=True)
    project_id: PropertyRef = PropertyRef("project_id")
    rotation_enabled: PropertyRef = PropertyRef("rotation_enabled")
    rotation_period: PropertyRef = PropertyRef("rotation_period")
    rotation_next_time: PropertyRef = PropertyRef("rotation_next_time")
    created_date: PropertyRef = PropertyRef("created_date")
    expire_time: PropertyRef = PropertyRef("expire_time")
    replication_type: PropertyRef = PropertyRef("replication_type")
    etag: PropertyRef = PropertyRef("etag")
    labels: PropertyRef = PropertyRef("labels")
    topics: PropertyRef = PropertyRef("topics")
    version_aliases: PropertyRef = PropertyRef("version_aliases")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class GCPSecretManagerSecretRelProperties(CartographyRelProperties):
    """
    Properties for relationships between Secret and other nodes
    """

    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class GCPSecretManagerSecretToProjectRel(CartographyRelSchema):
    """
    Relationship between Secret and GCP Project
    (:GCPProject)-[:RESOURCE]->(:GCPSecretManagerSecret)
    """

    target_node_label: str = "GCPProject"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("PROJECT_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: GCPSecretManagerSecretRelProperties = (
        GCPSecretManagerSecretRelProperties()
    )


@dataclass(frozen=True)
class GCPSecretManagerSecretSchema(CartographyNodeSchema):
    """
    Schema for GCP Secret Manager Secret
    """

    label: str = "GCPSecretManagerSecret"
    properties: GCPSecretManagerSecretNodeProperties = (
        GCPSecretManagerSecretNodeProperties()
    )
    sub_resource_relationship: GCPSecretManagerSecretToProjectRel = (
        GCPSecretManagerSecretToProjectRel()
    )

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
class GCPSecretManagerSecretVersionNodeProperties(CartographyNodeProperties):
    """
    Properties for GCP Secret Manager Secret Version
    """

    id: PropertyRef = PropertyRef("id")
    secret_id: PropertyRef = PropertyRef("secret_id")
    version: PropertyRef = PropertyRef("version")
    state: PropertyRef = PropertyRef("state")

    # Date properties (epoch timestamps)
    created_date: PropertyRef = PropertyRef("created_date")
    destroy_time: PropertyRef = PropertyRef("destroy_time")

    # Other properties
    etag: PropertyRef = PropertyRef("etag")

    # Standard cartography properties
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class GCPSecretManagerSecretVersionRelProperties(CartographyRelProperties):
    """
    Properties for relationships between Secret Version and other nodes
    """

    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class GCPSecretManagerSecretVersionToProjectRel(CartographyRelSchema):
    """
    Relationship between Secret Version and GCP Project
    (:GCPProject)-[:RESOURCE]->(:GCPSecretManagerSecretVersion)
    """

    target_node_label: str = "GCPProject"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("PROJECT_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: GCPSecretManagerSecretVersionRelProperties = (
        GCPSecretManagerSecretVersionRelProperties()
    )


@dataclass(frozen=True)
class GCPSecretManagerSecretVersionToSecretRel(CartographyRelSchema):
    """
    Relationship between Secret Version and its parent Secret
    (:GCPSecretManagerSecretVersion)-[:VERSION_OF]->(:GCPSecretManagerSecret)
    """

    target_node_label: str = "GCPSecretManagerSecret"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("secret_id")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "VERSION_OF"
    properties: GCPSecretManagerSecretVersionRelProperties = (
        GCPSecretManagerSecretVersionRelProperties()
    )


@dataclass(frozen=True)
class GCPSecretManagerSecretVersionSchema(CartographyNodeSchema):
    """
    Schema for GCP Secret Manager Secret Version
    """

    label: str = "GCPSecretManagerSecretVersion"
    properties: GCPSecretManagerSecretVersionNodeProperties = (
        GCPSecretManagerSecretVersionNodeProperties()
    )
    sub_resource_relationship: GCPSecretManagerSecretVersionToProjectRel = (
        GCPSecretManagerSecretVersionToProjectRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            GCPSecretManagerSecretVersionToSecretRel(),
        ],
    )

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
class ScalewayServerlessFunctionNamespaceProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id", extra_index=True)
    name: PropertyRef = PropertyRef("name", extra_index=True)
    description: PropertyRef = PropertyRef("description")
    status: PropertyRef = PropertyRef("status")
    error_message: PropertyRef = PropertyRef("error_message")
    registry_namespace_id: PropertyRef = PropertyRef("registry_namespace_id")
    registry_endpoint: PropertyRef = PropertyRef("registry_endpoint", extra_index=True)
    # Whether the namespace can reach a VPC private network.
    vpc_integration_activated: PropertyRef = PropertyRef("vpc_integration_activated")
    region: PropertyRef = PropertyRef("region")
    tags: PropertyRef = PropertyRef("tags")
    created_at: PropertyRef = PropertyRef("created_at")
    updated_at: PropertyRef = PropertyRef("updated_at")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class ScalewayServerlessFunctionNamespaceToProjectRelProperties(
    CartographyRelProperties
):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:ScalewayProject)-[:RESOURCE]->(:ScalewayServerlessFunctionNamespace)
class ScalewayServerlessFunctionNamespaceToProjectRel(CartographyRelSchema):
    target_node_label: str = "ScalewayProject"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("PROJECT_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: ScalewayServerlessFunctionNamespaceToProjectRelProperties = (
        ScalewayServerlessFunctionNamespaceToProjectRelProperties()
    )


@dataclass(frozen=True)
class ScalewayServerlessFunctionNamespaceSchema(CartographyNodeSchema):
    label: str = "ScalewayServerlessFunctionNamespace"
    properties: ScalewayServerlessFunctionNamespaceProperties = (
        ScalewayServerlessFunctionNamespaceProperties()
    )
    sub_resource_relationship: ScalewayServerlessFunctionNamespaceToProjectRel = (
        ScalewayServerlessFunctionNamespaceToProjectRel()
    )

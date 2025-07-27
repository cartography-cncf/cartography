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
class AirbyteWorkspaceNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("workspaceId")
    name: PropertyRef = PropertyRef("name")
    data_residency: PropertyRef = PropertyRef("dataResidency")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AirbyteWorkspaceToOrganizationRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:AirbyteOrganization)-[:RESOURCE]->(:AirbyteWorkspace)
class AirbyteWorkspaceToOrganizationRel(CartographyRelSchema):
    target_node_label: str = "AirbyteOrganization"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("ORG_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: AirbyteWorkspaceToOrganizationRelProperties = (
        AirbyteWorkspaceToOrganizationRelProperties()
    )


@dataclass(frozen=True)
class AirbyteWorkspaceSchema(CartographyNodeSchema):
    label: str = "AirbyteWorkspace"
    properties: AirbyteWorkspaceNodeProperties = AirbyteWorkspaceNodeProperties()
    sub_resource_relationship: AirbyteWorkspaceToOrganizationRel = (
        AirbyteWorkspaceToOrganizationRel()
    )

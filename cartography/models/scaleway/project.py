from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.nodes import ExtraNodeLabels
from cartography.models.core.relationships import CartographyRelProperties
from cartography.models.core.relationships import CartographyRelSchema
from cartography.models.core.relationships import LinkDirection
from cartography.models.core.relationships import make_target_node_matcher
from cartography.models.core.relationships import TargetNodeMatcher


@dataclass(frozen=True)
class ScalewayProjectNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id", description="ID of the Scaleway Project")
    name: PropertyRef = PropertyRef("name", description="Name of the project")
    created_at: PropertyRef = PropertyRef(
        "created_at", description="Creation timestamp"
    )
    updated_at: PropertyRef = PropertyRef(
        "updated_at", description="Last update timestamp"
    )
    description: PropertyRef = PropertyRef(
        "description", description="Project description"
    )
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated", set_in_kwargs=True, description="Timestamp of the last update"
    )


@dataclass(frozen=True)
class ScalewayProjectToOrganizationRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:ScalewayOrganization)-[:RESOURCE]->(:ScalewayProject)
class ScalewayProjectToOrganizationRel(CartographyRelSchema):
    """Connects `ScalewayOrganization` to `ScalewayProject` through `RESOURCE`."""

    target_node_label: str = "ScalewayOrganization"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("ORG_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: ScalewayProjectToOrganizationRelProperties = (
        ScalewayProjectToOrganizationRelProperties()
    )


@dataclass(frozen=True)
class ScalewayProjectSchema(CartographyNodeSchema):
    """Represents a Project in Scaleway. Projects are groupings of Scaleway resources."""

    label: str = "ScalewayProject"
    properties: ScalewayProjectNodeProperties = ScalewayProjectNodeProperties()
    sub_resource_relationship: ScalewayProjectToOrganizationRel = (
        ScalewayProjectToOrganizationRel()
    )
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(["Tenant"])

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
class ScalewayApplicationNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id", description="ID of the application.")
    name: PropertyRef = PropertyRef("name", description="Name of the application.")
    description: PropertyRef = PropertyRef(
        "description", description="Description of the application."
    )
    created_at: PropertyRef = PropertyRef(
        "created_at", description="Date and time application was created."
    )
    updated_at: PropertyRef = PropertyRef(
        "updated_at", description="Date and time of last application update."
    )
    editable: PropertyRef = PropertyRef(
        "editable", description="Defines whether or not the application is editable."
    )
    deletable: PropertyRef = PropertyRef(
        "deletable", description="Defines whether or not the application is deletable."
    )
    managed: PropertyRef = PropertyRef(
        "managed", description="Defines whether or not the application is managed."
    )
    tags: PropertyRef = PropertyRef(
        "tags", description="Tags associated with the user."
    )
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated", set_in_kwargs=True, description="Timestamp of the last update"
    )


@dataclass(frozen=True)
class ScalewayApplicationToOrganizationRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:ScalewayOrganization)-[:RESOURCE]->(:ScalewayApplication)
class ScalewayApplicationToOrganizationRel(CartographyRelSchema):
    """Connects `ScalewayOrganization` to `ScalewayApplication` through `RESOURCE`."""

    target_node_label: str = "ScalewayOrganization"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("ORG_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: ScalewayApplicationToOrganizationRelProperties = (
        ScalewayApplicationToOrganizationRelProperties()
    )


@dataclass(frozen=True)
class ScalewayApplicationSchema(CartographyNodeSchema):
    """Represents an Application (Service Account) in Scaleway"""

    label: str = "ScalewayApplication"
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(["ServiceAccount"])
    properties: ScalewayApplicationNodeProperties = ScalewayApplicationNodeProperties()
    sub_resource_relationship: ScalewayApplicationToOrganizationRel = (
        ScalewayApplicationToOrganizationRel()
    )

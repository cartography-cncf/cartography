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
class ScalewayPermissionSetNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id", description="ID of the permission set.")
    name: PropertyRef = PropertyRef(
        "name", extra_index=True, description="Name of the permission set."
    )
    scope_type: PropertyRef = PropertyRef(
        "scope_type", description="Scope type of the permission set."
    )
    description: PropertyRef = PropertyRef(
        "description", description="Description of the permission set."
    )
    categories: PropertyRef = PropertyRef(
        "categories", description="Categories of the permission set."
    )
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated", set_in_kwargs=True, description="Timestamp of the last update"
    )


@dataclass(frozen=True)
class ScalewayPermissionSetToOrganizationRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:ScalewayOrganization)-[:RESOURCE]->(:ScalewayPermissionSet)
class ScalewayPermissionSetToOrganizationRel(CartographyRelSchema):
    """Connects `ScalewayOrganization` to `ScalewayPermissionSet` through `RESOURCE`."""

    target_node_label: str = "ScalewayOrganization"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("ORG_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: ScalewayPermissionSetToOrganizationRelProperties = (
        ScalewayPermissionSetToOrganizationRelProperties()
    )


@dataclass(frozen=True)
class ScalewayPermissionSetSchema(CartographyNodeSchema):
    """Represents a Permission Set in Scaleway. Permission sets are predefined collections
    of permissions.
    """

    label: str = "ScalewayPermissionSet"
    properties: ScalewayPermissionSetNodeProperties = (
        ScalewayPermissionSetNodeProperties()
    )
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(["PermissionRole"])
    sub_resource_relationship: ScalewayPermissionSetToOrganizationRel = (
        ScalewayPermissionSetToOrganizationRel()
    )

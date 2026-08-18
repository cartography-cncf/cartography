from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.nodes import ExtraNodeLabels
from cartography.models.core.relationships import CartographyRelProperties
from cartography.models.core.relationships import CartographyRelSchema
from cartography.models.core.relationships import LinkDirection
from cartography.models.core.relationships import make_source_node_matcher
from cartography.models.core.relationships import make_target_node_matcher
from cartography.models.core.relationships import SourceNodeMatcher
from cartography.models.core.relationships import TargetNodeMatcher
from cartography.models.ontology.labels import USER_ACCOUNT


@dataclass(frozen=True)
class FlyUserNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id", description="Fly user ID.")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    name: PropertyRef = PropertyRef("name", description="User display name.")
    email: PropertyRef = PropertyRef(
        "email", extra_index=True, description="User email address."
    )


@dataclass(frozen=True)
class FlyUserMemberOfOrganizationRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    _sub_resource_label: PropertyRef = PropertyRef(
        "_sub_resource_label",
        set_in_kwargs=True,
    )
    _sub_resource_id: PropertyRef = PropertyRef("_sub_resource_id", set_in_kwargs=True)
    role: PropertyRef = PropertyRef(
        "role", description="User role in the organization."
    )
    joined_at: PropertyRef = PropertyRef(
        "joined_at", description="Timestamp when the user joined the organization."
    )


@dataclass(frozen=True)
# (:FlyUser)-[:MEMBER_OF]->(:FlyOrganization)
class FlyUserToOrganizationMemberMatchLink(CartographyRelSchema):
    """Connects `FlyUser` to a Fly organization membership."""

    source_node_label: str = "FlyUser"
    source_node_matcher: SourceNodeMatcher = make_source_node_matcher(
        {"id": PropertyRef("id")},
    )
    target_node_label: str = "FlyOrganization"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("organization_id")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "MEMBER_OF"
    properties: FlyUserMemberOfOrganizationRelProperties = (
        FlyUserMemberOfOrganizationRelProperties()
    )


@dataclass(frozen=True)
class FlyUserToOrganizationRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    _sub_resource_label: PropertyRef = PropertyRef(
        "_sub_resource_label",
        set_in_kwargs=True,
    )
    _sub_resource_id: PropertyRef = PropertyRef("_sub_resource_id", set_in_kwargs=True)


@dataclass(frozen=True)
# (:FlyOrganization)-[:RESOURCE]->(:FlyUser)
class FlyUserToOrganizationResourceMatchLink(CartographyRelSchema):
    """Connects `FlyOrganization` to a shared `FlyUser` identity."""

    source_node_label: str = "FlyUser"
    source_node_matcher: SourceNodeMatcher = make_source_node_matcher(
        {"id": PropertyRef("id")},
    )
    target_node_label: str = "FlyOrganization"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("organization_id")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: FlyUserToOrganizationRelProperties = (
        FlyUserToOrganizationRelProperties()
    )


@dataclass(frozen=True)
class FlyUserSchema(CartographyNodeSchema):
    """Represents a Fly.io user identity shared across organization scopes."""

    label: str = "FlyUser"
    properties: FlyUserNodeProperties = FlyUserNodeProperties()
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels([USER_ACCOUNT])

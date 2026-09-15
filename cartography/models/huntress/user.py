from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.nodes import ExtraNodeLabels
from cartography.models.core.relationships import CartographyRelProperties
from cartography.models.core.relationships import CartographyRelSchema
from cartography.models.core.relationships import LinkDirection
from cartography.models.core.relationships import make_target_node_matcher
from cartography.models.core.relationships import OtherRelationships
from cartography.models.core.relationships import TargetNodeMatcher
from cartography.models.ontology.labels import USER_ACCOUNT


@dataclass(frozen=True)
class HuntressUserNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "id",
        description="Huntress-unique identifier for the user.",
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    email: PropertyRef = PropertyRef(
        "email",
        extra_index=True,
        description="Email address the user signs in to the Huntress console with.",
    )
    name: PropertyRef = PropertyRef(
        "name",
        extra_index=True,
        description="Display name of the user.",
    )


@dataclass(frozen=True)
class HuntressUserToAccountRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


# (:HuntressAccount)-[:RESOURCE]->(:HuntressUser)
@dataclass(frozen=True)
class HuntressUserToAccountRel(CartographyRelSchema):
    """Links a Huntress account to one of the users with access to its console."""

    target_node_label: str = "HuntressAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("ACCOUNT_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: HuntressUserToAccountRelProperties = (
        HuntressUserToAccountRelProperties()
    )


@dataclass(frozen=True)
class HuntressUserToRoleRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


# (:HuntressUser)-[:HAS_ROLE]->(:HuntressRole)
@dataclass(frozen=True)
class HuntressUserToRoleRel(CartographyRelSchema):
    """Links a Huntress user to a console role granted to them."""

    target_node_label: str = "HuntressRole"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("role_ids", one_to_many=True)},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "HAS_ROLE"
    properties: HuntressUserToRoleRelProperties = HuntressUserToRoleRelProperties()


@dataclass(frozen=True)
class HuntressUserToOrganizationRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


# (:HuntressUser)-[:MEMBER_OF]->(:HuntressOrganization)
@dataclass(frozen=True)
class HuntressUserToOrganizationRel(CartographyRelSchema):
    """Links a Huntress user to an organization they hold a membership in."""

    target_node_label: str = "HuntressOrganization"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("organization_ids", one_to_many=True)},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "MEMBER_OF"
    properties: HuntressUserToOrganizationRelProperties = (
        HuntressUserToOrganizationRelProperties()
    )


@dataclass(frozen=True)
class HuntressUserSchema(CartographyNodeSchema):
    """A user with access to the Huntress console, derived from their memberships."""

    label: str = "HuntressUser"
    properties: HuntressUserNodeProperties = HuntressUserNodeProperties()
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels([USER_ACCOUNT])
    sub_resource_relationship: HuntressUserToAccountRel = HuntressUserToAccountRel()
    other_relationships: OtherRelationships = OtherRelationships(
        [
            HuntressUserToRoleRel(),
            HuntressUserToOrganizationRel(),
        ],
    )

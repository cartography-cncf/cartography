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
class PylonUserNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id", description="Pylon user ID.")
    name: PropertyRef = PropertyRef("name", description="User name.")
    email: PropertyRef = PropertyRef(
        "email",
        extra_index=True,
        description="Primary email address of the user.",
    )
    emails: PropertyRef = PropertyRef(
        "emails",
        description="All email addresses of the user.",
    )
    is_deactivated: PropertyRef = PropertyRef(
        "is_deactivated",
        description=(
            "Whether the user is deactivated. A deactivated user can't sign in, "
            "and Pylon deletes the API tokens that the user created."
        ),
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class PylonUserToOrganizationRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:PylonOrganization)-[:RESOURCE]->(:PylonUser)
class PylonUserToOrganizationRel(CartographyRelSchema):
    """The organization contains the user."""

    target_node_label: str = "PylonOrganization"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("ORG_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: PylonUserToOrganizationRelProperties = (
        PylonUserToOrganizationRelProperties()
    )


@dataclass(frozen=True)
class PylonUserToRoleRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:PylonUser)-[:HAS_ROLE]->(:PylonRole)
class PylonUserToRoleRel(CartographyRelSchema):
    """The user is assigned the role, directly or through a SCIM group mapping."""

    target_node_label: str = "PylonRole"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("role_ids", one_to_many=True)},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "HAS_ROLE"
    properties: PylonUserToRoleRelProperties = PylonUserToRoleRelProperties()


@dataclass(frozen=True)
class PylonUserSchema(CartographyNodeSchema):
    """A person's account in a Pylon organization, read from `GET /users`.

    Cartography includes deactivated users so that stale access stays visible.
    Entries without an email address are API tokens or bots, which Cartography
    loads as `PylonServiceAccount` instead. The `UserAccount` label links the
    user to the canonical `User` node by email address.
    """

    label: str = "PylonUser"
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels([USER_ACCOUNT])
    properties: PylonUserNodeProperties = PylonUserNodeProperties()
    sub_resource_relationship: PylonUserToOrganizationRel = PylonUserToOrganizationRel()
    other_relationships: OtherRelationships = OtherRelationships(
        [PylonUserToRoleRel()],
    )

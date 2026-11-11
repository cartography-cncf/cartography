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
from cartography.models.onepassword.account import OnePasswordAccountToResourceRel
from cartography.models.ontology.labels import SERVICE_ACCOUNT
from cartography.models.ontology.labels import USER_ACCOUNT


@dataclass(frozen=True)
class OnePasswordUserNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id", description="1Password user UUID.")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    name: PropertyRef = PropertyRef("name", description="Display name of the user.")
    email: PropertyRef = PropertyRef(
        "email",
        extra_index=True,
        description="Email address of the user.",
    )
    state: PropertyRef = PropertyRef(
        "state",
        description=(
            "Account state reported by 1Password, such as `ACTIVE`, `PENDING`, "
            "or `SUSPENDED`."
        ),
    )
    type: PropertyRef = PropertyRef(
        "type",
        description="User type reported by 1Password, such as `MEMBER` or `GUEST`.",
    )


@dataclass(frozen=True)
class OnePasswordServiceAccountNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id", description="1Password service account UUID.")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    name: PropertyRef = PropertyRef(
        "name",
        description=(
            "Display name of the service account. 1Password omits it for the "
            "collector's own service account."
        ),
    )
    state: PropertyRef = PropertyRef(
        "state",
        description="Service account state reported by 1Password, such as `ACTIVE`.",
    )


@dataclass(frozen=True)
class OnePasswordMemberOfGroupRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:OnePasswordUser|OnePasswordServiceAccount)-[:MEMBER_OF]->(:OnePasswordGroup)
class OnePasswordMemberOfGroupRel(CartographyRelSchema):
    """Membership of a user or service account in a 1Password group."""

    target_node_label: str = "OnePasswordGroup"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("group_ids", one_to_many=True)},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "MEMBER_OF"
    properties: OnePasswordMemberOfGroupRelProperties = (
        OnePasswordMemberOfGroupRelProperties()
    )


@dataclass(frozen=True)
class OnePasswordUserSchema(CartographyNodeSchema):
    """A person's account in 1Password, including guests and pending invitations."""

    label: str = "OnePasswordUser"
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels([USER_ACCOUNT])
    properties: OnePasswordUserNodeProperties = OnePasswordUserNodeProperties()
    sub_resource_relationship: OnePasswordAccountToResourceRel = (
        OnePasswordAccountToResourceRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [OnePasswordMemberOfGroupRel()],
    )


@dataclass(frozen=True)
class OnePasswordServiceAccountSchema(CartographyNodeSchema):
    """
    A 1Password service account: a non-human identity that automation uses to
    read or write vault items.
    """

    label: str = "OnePasswordServiceAccount"
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels([SERVICE_ACCOUNT])
    properties: OnePasswordServiceAccountNodeProperties = (
        OnePasswordServiceAccountNodeProperties()
    )
    sub_resource_relationship: OnePasswordAccountToResourceRel = (
        OnePasswordAccountToResourceRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [OnePasswordMemberOfGroupRel()],
    )

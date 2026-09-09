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
from cartography.models.ontology.labels import USER_ACCOUNT


@dataclass(frozen=True)
class OpsgenieUserNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id", description="Opsgenie user ID.")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    username: PropertyRef = PropertyRef(
        "username",
        extra_index=True,
        description="User email address.",
    )
    full_name: PropertyRef = PropertyRef(
        "full_name",
        description="User display name.",
    )
    role: PropertyRef = PropertyRef("role", description="User role name.")
    blocked: PropertyRef = PropertyRef(
        "blocked",
        description="Whether the user is blocked.",
    )
    verified: PropertyRef = PropertyRef(
        "verified",
        description="Whether the user is verified.",
    )
    timezone: PropertyRef = PropertyRef(
        "timezone",
        description="User time zone.",
    )
    locale: PropertyRef = PropertyRef("locale", description="User locale.")
    created_at: PropertyRef = PropertyRef(
        "created_at",
        description="ISO 8601 timestamp when the user was created.",
    )


@dataclass(frozen=True)
class OpsgenieAccountToUserRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class OpsgenieAccountToUserRel(CartographyRelSchema):
    """The account contains the user."""

    target_node_label: str = "OpsgenieAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("ACCOUNT_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: OpsgenieAccountToUserRelProperties = (
        OpsgenieAccountToUserRelProperties()
    )


@dataclass(frozen=True)
class OpsgenieUserSchema(CartographyNodeSchema):
    """A user in an Opsgenie account."""

    label: str = "OpsgenieUser"
    properties: OpsgenieUserNodeProperties = OpsgenieUserNodeProperties()
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels([USER_ACCOUNT])
    sub_resource_relationship: OpsgenieAccountToUserRel = OpsgenieAccountToUserRel()

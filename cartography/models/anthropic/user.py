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
class AnthropicUserNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id", description="Anthropic user ID.")
    name: PropertyRef = PropertyRef("name", description="User name.")
    email: PropertyRef = PropertyRef(
        "email",
        extra_index=True,
        description="User email address.",
    )
    role: PropertyRef = PropertyRef(
        "role",
        description="Organization role: admin or user.",
    )
    added_at: PropertyRef = PropertyRef(
        "added_at",
        description="RFC 3339 timestamp when the user was added.",
    )
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last update.",
    )


@dataclass(frozen=True)
class AnthropicUserToOrganizationRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:AnthropicOrganization)-[:RESOURCE]->(:AnthropicUser)
class AnthropicUserToOrganizationRel(CartographyRelSchema):
    """The organization contains the user."""

    target_node_label: str = "AnthropicOrganization"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("ORG_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: AnthropicUserToOrganizationRelProperties = (
        AnthropicUserToOrganizationRelProperties()
    )


@dataclass(frozen=True)
class AnthropicUserSchema(CartographyNodeSchema):
    """A user account in an Anthropic organization."""

    label: str = "AnthropicUser"
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(
        ["UserAccount"]
    )  # UserAccount label is used for ontology mapping
    properties: AnthropicUserNodeProperties = AnthropicUserNodeProperties()
    sub_resource_relationship: AnthropicUserToOrganizationRel = (
        AnthropicUserToOrganizationRel()
    )

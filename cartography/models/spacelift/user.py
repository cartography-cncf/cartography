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
class SpaceliftUserNodeProperties(CartographyNodeProperties):
    """
    Properties for a Spacelift User node.
    """

    id: PropertyRef = PropertyRef("id", description="Spacelift user ID.")
    username: PropertyRef = PropertyRef(
        "username", extra_index=True, description="User login name."
    )
    email: PropertyRef = PropertyRef(
        "email", extra_index=True, description="User email address."
    )
    name: PropertyRef = PropertyRef("name", description="User display name.")
    user_type: PropertyRef = PropertyRef(
        "user_type", description="Type of Spacelift user, such as human or machine."
    )
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last update.",
    )


@dataclass(frozen=True)
class SpaceliftUserToAccountRelProperties(CartographyRelProperties):
    """
    Properties for the RESOURCE relationship between a User and its Account.
    """

    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class SpaceliftUserToAccountRel(CartographyRelSchema):
    """A Spacelift account contains a user."""

    target_node_label: str = "SpaceliftAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("spacelift_account_id", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: SpaceliftUserToAccountRelProperties = (
        SpaceliftUserToAccountRelProperties()
    )


@dataclass(frozen=True)
class SpaceliftUserSchema(CartographyNodeSchema):
    """A Spacelift identity with the UserAccount label."""

    label: str = "SpaceliftUser"
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(
        ["UserAccount"]
    )  # UserAccount label is used for ontology mapping
    properties: SpaceliftUserNodeProperties = SpaceliftUserNodeProperties()
    sub_resource_relationship: SpaceliftUserToAccountRel = SpaceliftUserToAccountRel()
    other_relationships = None

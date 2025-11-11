from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
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

    id: PropertyRef = PropertyRef("id")
    username: PropertyRef = PropertyRef("username", extra_index=True)
    email: PropertyRef = PropertyRef("email", extra_index=True)
    name: PropertyRef = PropertyRef("name")
    user_type: PropertyRef = PropertyRef("user_type")  # e.g., "human" or "machine"
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class SpaceliftUserToAccountRelProperties(CartographyRelProperties):
    """
    Properties for the RESOURCE relationship between a User and its Account.
    """

    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class SpaceliftUserToAccountRel(CartographyRelSchema):
    """
    RESOURCE relationship from a User to its Account.
    (:SpaceliftUser)<-[:RESOURCE]-(:SpaceliftAccount)
    """

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
    """
    Schema for a Spacelift User node.
    """

    label: str = "SpaceliftUser"
    properties: SpaceliftUserNodeProperties = SpaceliftUserNodeProperties()
    sub_resource_relationship: SpaceliftUserToAccountRel = SpaceliftUserToAccountRel()
    other_relationships = None

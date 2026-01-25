from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.relationships import CartographyRelProperties
from cartography.models.core.relationships import CartographyRelSchema
from cartography.models.core.relationships import LinkDirection
from cartography.models.core.relationships import make_target_node_matcher
from cartography.models.core.relationships import OtherRelationships
from cartography.models.core.relationships import TargetNodeMatcher


@dataclass(frozen=True)
class SpaceliftSpaceNodeProperties(CartographyNodeProperties):
    """
    Properties for a Spacelift Space node.
    """

    id: PropertyRef = PropertyRef("id")
    name: PropertyRef = PropertyRef("name", extra_index=True)
    description: PropertyRef = PropertyRef("description")
    is_root: PropertyRef = PropertyRef("is_root")
    spacelift_account_id: PropertyRef = PropertyRef(
        "spacelift_account_id"
    )  # spacelift_account_id is set for ALL spaces (root and nested) for RESOURCE relationship
    parent_spacelift_account_id: PropertyRef = PropertyRef(
        "parent_spacelift_account_id"
    )  # parent_spacelift_account_id is set ONLY for root spaces (identifies hierarchy root)
    parent_space_id: PropertyRef = PropertyRef(
        "parent_space_id"
    )  # parent_space_id is set ONLY for child spaces (identifies hierarchy parent)
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class SpaceliftSpaceToAccountRelProperties(CartographyRelProperties):
    """
    Properties for the RESOURCE relationship between a Space and its Account.
    """

    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class SpaceliftSpaceToAccountRel(CartographyRelSchema):
    """
    RESOURCE relationship from any Space to its Account.
    (:SpaceliftSpace)<-[:RESOURCE]-(:SpaceliftAccount)
    """

    target_node_label: str = "SpaceliftAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("spacelift_account_id", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: SpaceliftSpaceToAccountRelProperties = (
        SpaceliftSpaceToAccountRelProperties()
    )


@dataclass(frozen=True)
class SpaceliftSpaceToSpaceRelProperties(CartographyRelProperties):
    """
    Properties for the CONTAINS relationship between a child Space and its parent Space.
    """

    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class SpaceliftSpaceToSpaceRel(CartographyRelSchema):
    """
    CONTAINS relationship from a child Space to its parent Space.
    (:SpaceliftSpace)<-[:CONTAINS]-(:SpaceliftSpace)
    """

    target_node_label: str = "SpaceliftSpace"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("parent_space_id")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "CONTAINS"
    properties: SpaceliftSpaceToSpaceRelProperties = (
        SpaceliftSpaceToSpaceRelProperties()
    )


@dataclass(frozen=True)
class SpaceliftUserToSpaceRelProperties(CartographyRelProperties):
    """
    Properties for the HAS_ROLE_IN relationship between a User and a Space.
    Includes the role the user has in that space (e.g., "admin", "read", "write").
    """

    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    role: PropertyRef = PropertyRef("role")


@dataclass(frozen=True)
class SpaceliftUserToSpaceRel(CartographyRelSchema):
    """
    HAS_ROLE_IN relationship from a User to a Space.
    (:SpaceliftUser)-[:HAS_ROLE_IN]->(:SpaceliftSpace)
    """

    target_node_label: str = "SpaceliftSpace"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("space_id")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "HAS_ROLE_IN"
    properties: SpaceliftUserToSpaceRelProperties = SpaceliftUserToSpaceRelProperties()


@dataclass(frozen=True)
class SpaceliftSpaceSchema(CartographyNodeSchema):
    """
    Schema for a Spacelift Space node.
    """

    label: str = "SpaceliftSpace"
    properties: SpaceliftSpaceNodeProperties = SpaceliftSpaceNodeProperties()
    sub_resource_relationship: SpaceliftSpaceToAccountRel = SpaceliftSpaceToAccountRel()
    other_relationships: OtherRelationships = OtherRelationships(
        [
            SpaceliftSpaceToSpaceRel(),
            SpaceliftUserToSpaceRel(),
        ],
    )

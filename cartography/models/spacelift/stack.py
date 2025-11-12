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
class SpaceliftStackNodeProperties(CartographyNodeProperties):
    """
    Properties for a Spacelift Stack node.
    """

    id: PropertyRef = PropertyRef("id")
    name: PropertyRef = PropertyRef("name", extra_index=True)
    description: PropertyRef = PropertyRef("description")
    state: PropertyRef = PropertyRef("state")
    administrative: PropertyRef = PropertyRef("administrative")
    repository: PropertyRef = PropertyRef("repository")
    branch: PropertyRef = PropertyRef("branch")
    project_root: PropertyRef = PropertyRef("project_root")  # Directory in repo
    space_id: PropertyRef = PropertyRef("space_id")
    spacelift_account_id: PropertyRef = PropertyRef("spacelift_account_id")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class SpaceliftStackToAccountRelProperties(CartographyRelProperties):
    """
    Properties for the RESOURCE relationship between a Stack and its Account.
    """

    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class SpaceliftStackToAccountRel(CartographyRelSchema):
    """
    RESOURCE relationship from a Stack to its Account.
    (:SpaceliftStack)<-[:RESOURCE]-(:SpaceliftAccount)
    """

    target_node_label: str = "SpaceliftAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("spacelift_account_id", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: SpaceliftStackToAccountRelProperties = (
        SpaceliftStackToAccountRelProperties()
    )


@dataclass(frozen=True)
class SpaceliftStackToSpaceRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class SpaceliftStackToSpaceRel(CartographyRelSchema):
    """
    CONTAINS relationship from a Stack to its parent Space.
    (:SpaceliftStack)<-[:CONTAINS]-(:SpaceliftSpace)
    """

    target_node_label: str = "SpaceliftSpace"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("space_id")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "CONTAINS"
    properties: SpaceliftStackToSpaceRelProperties = (
        SpaceliftStackToSpaceRelProperties()
    )


@dataclass(frozen=True)
class SpaceliftStackSchema(CartographyNodeSchema):
    """
    Schema for a Spacelift Stack node.
    """

    label: str = "SpaceliftStack"
    properties: SpaceliftStackNodeProperties = SpaceliftStackNodeProperties()
    sub_resource_relationship: SpaceliftStackToAccountRel = SpaceliftStackToAccountRel()
    other_relationships: OtherRelationships = OtherRelationships(
        [
            SpaceliftStackToSpaceRel(),
        ],
    )

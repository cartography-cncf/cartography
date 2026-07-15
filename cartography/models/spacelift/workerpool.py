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
class SpaceliftWorkerPoolNodeProperties(CartographyNodeProperties):
    """
    Properties for a Spacelift Worker Pool node.
    """

    id: PropertyRef = PropertyRef("id", description="Spacelift worker pool ID.")
    name: PropertyRef = PropertyRef(
        "name", extra_index=True, description="Worker pool name."
    )
    description: PropertyRef = PropertyRef(
        "description", description="Worker pool description."
    )
    pool_type: PropertyRef = PropertyRef(
        "pool_type", description="Type of worker pool."
    )
    space_id: PropertyRef = PropertyRef(
        "space_id", description="ID of the space containing the worker pool."
    )
    spacelift_account_id: PropertyRef = PropertyRef(
        "spacelift_account_id", description="ID of the containing Spacelift account."
    )
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last update.",
    )


@dataclass(frozen=True)
class SpaceliftWorkerPoolToAccountRelProperties(CartographyRelProperties):
    """
    Properties for the RESOURCE relationship between a Worker Pool and its Account.
    """

    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class SpaceliftWorkerPoolToAccountRel(CartographyRelSchema):
    """A Spacelift account contains a worker pool."""

    target_node_label: str = "SpaceliftAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("spacelift_account_id", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: SpaceliftWorkerPoolToAccountRelProperties = (
        SpaceliftWorkerPoolToAccountRelProperties()
    )


@dataclass(frozen=True)
class SpaceliftWorkerPoolToSpaceRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class SpaceliftWorkerPoolToSpaceRel(CartographyRelSchema):
    """A Spacelift space contains a worker pool."""

    target_node_label: str = "SpaceliftSpace"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("space_id")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "CONTAINS"
    properties: SpaceliftWorkerPoolToSpaceRelProperties = (
        SpaceliftWorkerPoolToSpaceRelProperties()
    )


@dataclass(frozen=True)
class SpaceliftWorkerPoolSchema(CartographyNodeSchema):
    """A pool of workers that execute Spacelift runs."""

    label: str = "SpaceliftWorkerPool"
    properties: SpaceliftWorkerPoolNodeProperties = SpaceliftWorkerPoolNodeProperties()
    sub_resource_relationship: SpaceliftWorkerPoolToAccountRel = (
        SpaceliftWorkerPoolToAccountRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            SpaceliftWorkerPoolToSpaceRel(),
        ],
    )

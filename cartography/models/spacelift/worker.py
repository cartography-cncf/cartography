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
class SpaceliftWorkerNodeProperties(CartographyNodeProperties):
    """
    Properties for a Spacelift Worker node.
    """

    id: PropertyRef = PropertyRef("id")
    name: PropertyRef = PropertyRef("name", extra_index=True)
    status: PropertyRef = PropertyRef("status")
    worker_pool_id: PropertyRef = PropertyRef("worker_pool_id")
    spacelift_account_id: PropertyRef = PropertyRef("spacelift_account_id")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class SpaceliftWorkerToAccountRelProperties(CartographyRelProperties):
    """
    Properties for the RESOURCE relationship between a Worker and its Account.
    """

    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class SpaceliftWorkerToAccountRel(CartographyRelSchema):
    """
    RESOURCE relationship from a Worker to its Account.
    (:SpaceliftWorker)<-[:RESOURCE]-(:SpaceliftAccount)
    """

    target_node_label: str = "SpaceliftAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("spacelift_account_id", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: SpaceliftWorkerToAccountRelProperties = (
        SpaceliftWorkerToAccountRelProperties()
    )


@dataclass(frozen=True)
class SpaceliftWorkerToWorkerPoolRelProperties(CartographyRelProperties):
    """
    Properties for the CONTAINS relationship between a Worker Pool and its Worker.
    """

    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class SpaceliftWorkerToWorkerPoolRel(CartographyRelSchema):
    """
    CONTAINS relationship from a Worker to its parent Worker Pool.
    (:SpaceliftWorker)<-[:CONTAINS]-(:SpaceliftWorkerPool)
    """

    target_node_label: str = "SpaceliftWorkerPool"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("worker_pool_id")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "CONTAINS"
    properties: SpaceliftWorkerToWorkerPoolRelProperties = (
        SpaceliftWorkerToWorkerPoolRelProperties()
    )


@dataclass(frozen=True)
class SpaceliftWorkerSchema(CartographyNodeSchema):
    """
    Schema for a Spacelift Worker node.
    """

    label: str = "SpaceliftWorker"
    properties: SpaceliftWorkerNodeProperties = SpaceliftWorkerNodeProperties()
    sub_resource_relationship: SpaceliftWorkerToAccountRel = (
        SpaceliftWorkerToAccountRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            SpaceliftWorkerToWorkerPoolRel(),
        ],
    )

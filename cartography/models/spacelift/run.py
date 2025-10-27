"""
Spacelift Run data model.

A SpaceliftRun represents a job that can touch infrastructure. It is the execution instance
of a stack's configuration. Runs track the entire lifecycle from creation through execution
to completion, including state changes, outputs, and resource modifications.
"""

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
class SpaceliftRunNodeProperties(CartographyNodeProperties):
    """
    Properties for a Spacelift Run node.
    """
    id: PropertyRef = PropertyRef("id")
    run_type: PropertyRef = PropertyRef("run_type")
    state: PropertyRef = PropertyRef("state")
    commit_sha: PropertyRef = PropertyRef("commit_sha")
    branch: PropertyRef = PropertyRef("branch")
    created_at: PropertyRef = PropertyRef("created_at")
    stack_id: PropertyRef = PropertyRef("stack_id")
    triggered_by_user_id: PropertyRef = PropertyRef("triggered_by_user_id")
    account_id: PropertyRef = PropertyRef("account_id")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class SpaceliftRunToAccountRelProperties(CartographyRelProperties):
    """
    Properties for the RESOURCE relationship between a Run and its Account.
    """
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class SpaceliftRunToAccountRel(CartographyRelSchema):
    """
    RESOURCE relationship from a Run to its Account.
    (:SpaceliftRun)<-[:RESOURCE]-(:SpaceliftAccount)
    """
    target_node_label: str = "SpaceliftAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("account_id", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: SpaceliftRunToAccountRelProperties = SpaceliftRunToAccountRelProperties()


@dataclass(frozen=True)
class SpaceliftRunToStackRelProperties(CartographyRelProperties):
    """
    Properties for the GENERATES relationship between a Stack and its Run.
    """
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class SpaceliftRunToStackRel(CartographyRelSchema):
    """
    GENERATES relationship from a Run to its parent Stack.
    (:SpaceliftRun)<-[:GENERATES]-(:SpaceliftStack)
    """
    target_node_label: str = "SpaceliftStack"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("stack_id")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "GENERATES"
    properties: SpaceliftRunToStackRelProperties = SpaceliftRunToStackRelProperties()


@dataclass(frozen=True)
class SpaceliftRunToUserRelProperties(CartographyRelProperties):
    """
    Properties for the TRIGGERED relationship between a User and a Run.
    """
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class SpaceliftRunToUserRel(CartographyRelSchema):
    """
    TRIGGERED relationship from a Run to the User who triggered it.
    (:SpaceliftRun)<-[:TRIGGERED]-(:SpaceliftUser)
    """
    target_node_label: str = "SpaceliftUser"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("triggered_by_user_id")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "TRIGGERED"
    properties: SpaceliftRunToUserRelProperties = SpaceliftRunToUserRelProperties()


@dataclass(frozen=True)
class SpaceliftRunToWorkerRelProperties(CartographyRelProperties):
    """
    Properties for the EXECUTES relationship between a Worker and a Run.
    """
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class SpaceliftRunToWorkerRel(CartographyRelSchema):
    """
    EXECUTES relationship from a Run to the Worker executing it.
    (:SpaceliftRun)<-[:EXECUTES]-(:SpaceliftWorker)
    """
    target_node_label: str = "SpaceliftWorker"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("worker_id")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "EXECUTES"
    properties: SpaceliftRunToWorkerRelProperties = SpaceliftRunToWorkerRelProperties()


@dataclass(frozen=True)
class SpaceliftRunToEC2InstanceRelProperties(CartographyRelProperties):
    """
    Properties for the AFFECTS relationship between a Run and EC2 Instances.
    """
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    action: PropertyRef = PropertyRef("action")  # e.g., "create", "update", "delete"


@dataclass(frozen=True)
class SpaceliftRunToEC2InstanceRel(CartographyRelSchema):
    """
    AFFECTS relationship from a Run to EC2 Instances it manages.
    (:SpaceliftRun)-[:AFFECTS]->(:EC2Instance)
    """
    target_node_label: str = "EC2Instance"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("affected_instance_ids", one_to_many=True)},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "AFFECTS"
    properties: SpaceliftRunToEC2InstanceRelProperties = SpaceliftRunToEC2InstanceRelProperties()


@dataclass(frozen=True)
class SpaceliftRunSchema(CartographyNodeSchema):
    """
    Schema for a Spacelift Run node.
    """
    label: str = "SpaceliftRun"
    properties: SpaceliftRunNodeProperties = SpaceliftRunNodeProperties()
    sub_resource_relationship: SpaceliftRunToAccountRel = SpaceliftRunToAccountRel()
    other_relationships: OtherRelationships = OtherRelationships(
        [
            SpaceliftRunToStackRel(),
            SpaceliftRunToUserRel(),
            SpaceliftRunToEC2InstanceRel(),
        ],
    )

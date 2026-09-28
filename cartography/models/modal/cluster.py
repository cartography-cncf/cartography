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
class ModalClusterNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id", description="Cluster ID.")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    app_id: PropertyRef = PropertyRef("app_id", description="ID of the owning app.")
    started_at: PropertyRef = PropertyRef(
        "started_at", description="When the cluster started."
    )
    task_ids: PropertyRef = PropertyRef(
        "task_ids",
        description="IDs of its member tasks. The edge itself is materialised from the task side.",
    )
    environment_name: PropertyRef = PropertyRef(
        "environment_name",
        extra_index=True,
        description="Name of the owning environment.",
    )


@dataclass(frozen=True)
class ModalClusterToEnvironmentRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:ModalEnvironment)-[:RESOURCE]->(:ModalCluster)
class ModalClusterToEnvironmentRel(CartographyRelSchema):
    target_node_label: str = "ModalEnvironment"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("ENVIRONMENT_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: ModalClusterToEnvironmentRelProperties = (
        ModalClusterToEnvironmentRelProperties()
    )


@dataclass(frozen=True)
class ModalClusterToAppRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:ModalCluster)-[:WORKLOAD_PARENT]->(:ModalApp)
class ModalClusterToAppRel(CartographyRelSchema):
    target_node_label: str = "ModalApp"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("app_id")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "WORKLOAD_PARENT"
    properties: ModalClusterToAppRelProperties = ModalClusterToAppRelProperties()


@dataclass(frozen=True)
# A Modal cluster groups the tasks of one multi-node job.
#
# It deliberately does NOT carry the ontology `ComputeCluster` label. That label is
# constrained against ComputePod and ComputeService (WORKLOAD_PARENT, enforced in both
# directions), which both the (:ModalTask)-[:MEMBER_OF]-> and
# (:ModalCluster)-[:WORKLOAD_PARENT]->(:ModalApp) edges would violate. A Modal cluster is
# also not a cluster in the ontology's sense (a durable compute substrate like EKS): it is a
# transient task grouping inside one app.
class ModalClusterSchema(CartographyNodeSchema):
    """Represents a Modal cluster: the group of tasks making up one multi-node job. This node deliberately carries **no** `ComputeCluster` ontology label. A Modal cluster is not a durable compute substrate like EKS, it is a transient task grouping inside a single app, and the label's ontology constraints against `ComputePod` and `ComputeService` would conflict with the `MEMBER_OF` and `WORKLOAD_PARENT` edges here."""

    label: str = "ModalCluster"
    properties: ModalClusterNodeProperties = ModalClusterNodeProperties()
    sub_resource_relationship: ModalClusterToEnvironmentRel = (
        ModalClusterToEnvironmentRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [ModalClusterToAppRel()]
    )

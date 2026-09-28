from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.nodes import ExtraNodeLabels
from cartography.models.core.relationships import CartographyRelProperties
from cartography.models.core.relationships import CartographyRelSchema
from cartography.models.core.relationships import LinkDirection
from cartography.models.core.relationships import make_target_node_matcher
from cartography.models.core.relationships import OtherRelationships
from cartography.models.core.relationships import TargetNodeMatcher
from cartography.models.ontology.labels import COMPUTE_POD


@dataclass(frozen=True)
class ModalTaskNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "id", description="Task ID, e.g. `ta-01KYQX24W4D7NW306JQ5D98X7S`."
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    app_id: PropertyRef = PropertyRef("app_id", description="ID of the owning app.")
    app_description: PropertyRef = PropertyRef(
        "app_description", description="Description of the owning app."
    )
    started_at: PropertyRef = PropertyRef(
        "started_at", description="When the task started running."
    )
    enqueued_at: PropertyRef = PropertyRef(
        "enqueued_at", description="When the task was enqueued."
    )
    cluster_id: PropertyRef = PropertyRef(
        "cluster_id", description="ID of the cluster it belongs to, if any."
    )
    environment_name: PropertyRef = PropertyRef(
        "environment_name",
        extra_index=True,
        description="Name of the owning environment.",
    )


@dataclass(frozen=True)
class ModalTaskToEnvironmentRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:ModalEnvironment)-[:RESOURCE]->(:ModalTask)
class ModalTaskToEnvironmentRel(CartographyRelSchema):
    target_node_label: str = "ModalEnvironment"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("ENVIRONMENT_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: ModalTaskToEnvironmentRelProperties = (
        ModalTaskToEnvironmentRelProperties()
    )


@dataclass(frozen=True)
class ModalTaskToAppRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:ModalTask)-[:WORKLOAD_PARENT]->(:ModalApp)
# WORKLOAD_PARENT is required here: ONTOLOGY_REL_CONSTRAINTS pins
# ComputePod -> ComputeService to this label.
class ModalTaskToAppRel(CartographyRelSchema):
    target_node_label: str = "ModalApp"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("app_id")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "WORKLOAD_PARENT"
    properties: ModalTaskToAppRelProperties = ModalTaskToAppRelProperties()


@dataclass(frozen=True)
class ModalTaskToClusterRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:ModalTask)-[:MEMBER_OF]->(:ModalCluster)
# Materialised from the task side rather than from ModalCluster.task_ids, so a task leaving a
# cluster cleans up with the task rather than needing the cluster to be re-synced.
class ModalTaskToClusterRel(CartographyRelSchema):
    target_node_label: str = "ModalCluster"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("cluster_id")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "MEMBER_OF"
    properties: ModalTaskToClusterRelProperties = ModalTaskToClusterRelProperties()


@dataclass(frozen=True)
# A running Modal container task. Only live tasks are returned by the API, so a task present
# in the graph is by construction running; that is why the ontology status is static.
class ModalTaskSchema(CartographyNodeSchema):
    """Represents a running Modal container task."""

    label: str = "ModalTask"
    properties: ModalTaskNodeProperties = ModalTaskNodeProperties()
    sub_resource_relationship: ModalTaskToEnvironmentRel = ModalTaskToEnvironmentRel()
    other_relationships: OtherRelationships = OtherRelationships(
        [ModalTaskToAppRel(), ModalTaskToClusterRel()],
    )
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels([COMPUTE_POD])

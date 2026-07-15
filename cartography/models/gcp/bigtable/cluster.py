import logging
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

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class GCPBigtableClusterProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "name", description="Stable identifier for this resource."
    )
    name: PropertyRef = PropertyRef(
        "name", description="The full resource name of the Bigtable Cluster."
    )
    location: PropertyRef = PropertyRef(
        "location",
        description="The GCP location where this cluster resides (e.g., `projects/.../locations/us-central1-b`).",
    )
    state: PropertyRef = PropertyRef(
        "state", description="The current state of the cluster (e.g., `READY`)."
    )
    default_storage_type: PropertyRef = PropertyRef(
        "defaultStorageType",
        description="Default Bigtable storage medium, such as SSD or HDD.",
    )
    instance_id: PropertyRef = PropertyRef(
        "instance_id",
        description="Identifier of the parent service instance.",
    )
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last time the node was updated.",
    )


@dataclass(frozen=True)
class ProjectToBigtableClusterRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last sync that observed this data.",
    )


@dataclass(frozen=True)
class ProjectToBigtableClusterRel(CartographyRelSchema):
    target_node_label: str = "GCPProject"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("PROJECT_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: ProjectToBigtableClusterRelProperties = (
        ProjectToBigtableClusterRelProperties()
    )


@dataclass(frozen=True)
class ClusterToInstanceRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last sync that observed this data.",
    )


@dataclass(frozen=True)
class ClusterToInstanceRel(CartographyRelSchema):
    target_node_label: str = "GCPBigtableInstance"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("instance_id")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "HAS_CLUSTER"
    properties: ClusterToInstanceRelProperties = ClusterToInstanceRelProperties()


@dataclass(frozen=True)
class GCPBigtableClusterSchema(CartographyNodeSchema):
    """Representation of a GCP [Bigtable Cluster](https://cloud.google.com/bigtable/docs/reference/admin/rest/v2/projects.instances.clusters)."""

    label: str = "GCPBigtableCluster"
    properties: GCPBigtableClusterProperties = GCPBigtableClusterProperties()
    sub_resource_relationship: ProjectToBigtableClusterRel = (
        ProjectToBigtableClusterRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            ClusterToInstanceRel(),
        ],
    )

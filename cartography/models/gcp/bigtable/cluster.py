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
    id: PropertyRef = PropertyRef("name")
    name: PropertyRef = PropertyRef("name")
    location: PropertyRef = PropertyRef("location")
    state: PropertyRef = PropertyRef("state")
    default_storage_type: PropertyRef = PropertyRef("defaultStorageType")
    instance_id: PropertyRef = PropertyRef("instance_id")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class ProjectToBigtableClusterRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


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
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


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

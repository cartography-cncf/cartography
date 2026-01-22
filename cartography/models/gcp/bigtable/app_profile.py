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
class GCPBigtableAppProfileProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("name")
    name: PropertyRef = PropertyRef("name")
    description: PropertyRef = PropertyRef("description")
    multi_cluster_routing_use_any: PropertyRef = PropertyRef(
        "multiClusterRoutingUseAny"
    )
    single_cluster_routing_cluster_id: PropertyRef = PropertyRef(
        "single_cluster_routing_cluster_id"
    )
    instance_id: PropertyRef = PropertyRef("instance_id")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class ProjectToBigtableAppProfileRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class ProjectToBigtableAppProfileRel(CartographyRelSchema):
    target_node_label: str = "GCPProject"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("PROJECT_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: ProjectToBigtableAppProfileRelProperties = (
        ProjectToBigtableAppProfileRelProperties()
    )


@dataclass(frozen=True)
class AppProfileToInstanceRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AppProfileToInstanceRel(CartographyRelSchema):
    target_node_label: str = "GCPBigtableInstance"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("instance_id")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "HAS_APP_PROFILE"
    properties: AppProfileToInstanceRelProperties = AppProfileToInstanceRelProperties()


@dataclass(frozen=True)
class AppProfileToClusterRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AppProfileToClusterRel(CartographyRelSchema):
    target_node_label: str = "GCPBigtableCluster"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("single_cluster_routing_cluster_id")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "ROUTES_TO"
    properties: AppProfileToClusterRelProperties = AppProfileToClusterRelProperties()


@dataclass(frozen=True)
class GCPBigtableAppProfileSchema(CartographyNodeSchema):
    label: str = "GCPBigtableAppProfile"
    properties: GCPBigtableAppProfileProperties = GCPBigtableAppProfileProperties()
    sub_resource_relationship: ProjectToBigtableAppProfileRel = (
        ProjectToBigtableAppProfileRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            AppProfileToInstanceRel(),
            AppProfileToClusterRel(),
        ],
    )

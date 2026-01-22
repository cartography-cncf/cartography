from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.relationships import CartographyRelProperties
from cartography.models.core.relationships import CartographyRelSchema
from cartography.models.core.relationships import LinkDirection
from cartography.models.core.relationships import make_target_node_matcher
from cartography.models.core.relationships import TargetNodeMatcher


@dataclass(frozen=True)
class KubernetesClusterRoleNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id")
    name: PropertyRef = PropertyRef("name")
    uid: PropertyRef = PropertyRef("uid")
    creation_timestamp: PropertyRef = PropertyRef("creation_timestamp")
    resource_version: PropertyRef = PropertyRef("resource_version")
    api_groups: PropertyRef = PropertyRef("api_groups")
    resources: PropertyRef = PropertyRef("resources")
    verbs: PropertyRef = PropertyRef("verbs")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class KubernetesClusterRoleToClusterRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class KubernetesClusterRoleToClusterRel(CartographyRelSchema):
    target_node_label: str = "KubernetesCluster"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("CLUSTER_ID", set_in_kwargs=True)}
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: KubernetesClusterRoleToClusterRelProperties = (
        KubernetesClusterRoleToClusterRelProperties()
    )


@dataclass(frozen=True)
class KubernetesClusterRoleSchema(CartographyNodeSchema):
    label: str = "KubernetesClusterRole"
    properties: KubernetesClusterRoleNodeProperties = (
        KubernetesClusterRoleNodeProperties()
    )
    sub_resource_relationship: KubernetesClusterRoleToClusterRel = (
        KubernetesClusterRoleToClusterRel()
    )

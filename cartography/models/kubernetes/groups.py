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
class KubernetesGroupNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id")
    name: PropertyRef = PropertyRef("name")
    cluster_name: PropertyRef = PropertyRef("cluster_name")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class KubernetesGroupToClusterRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class KubernetesGroupToClusterRel(CartographyRelSchema):
    target_node_label: str = "KubernetesCluster"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("CLUSTER_ID", set_in_kwargs=True)}
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: KubernetesGroupToClusterRelProperties = (
        KubernetesGroupToClusterRelProperties()
    )


@dataclass(frozen=True)
class KubernetesGroupToOktaGroupRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class KubernetesGroupToAWSRoleRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class KubernetesGroupToAWSUserRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class KubernetesGroupToOktaGroupRel(CartographyRelSchema):
    target_node_label: str = "OktaGroup"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"name": PropertyRef("name")}
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "MAPS_TO"
    properties: KubernetesGroupToOktaGroupRelProperties = (
        KubernetesGroupToOktaGroupRelProperties()
    )


@dataclass(frozen=True)
class KubernetesGroupToAWSRoleRel(CartographyRelSchema):
    target_node_label: str = "AWSRole"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"arn": PropertyRef("aws_role_arn")}
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "MAPS_TO"
    properties: KubernetesGroupToAWSRoleRelProperties = (
        KubernetesGroupToAWSRoleRelProperties()
    )


@dataclass(frozen=True)
class KubernetesGroupToAWSUserRel(CartographyRelSchema):
    target_node_label: str = "AWSUser"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"arn": PropertyRef("aws_user_arn")}
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "MAPS_TO"
    properties: KubernetesGroupToAWSUserRelProperties = (
        KubernetesGroupToAWSUserRelProperties()
    )


@dataclass(frozen=True)
class KubernetesGroupSchema(CartographyNodeSchema):
    label: str = "KubernetesGroup"
    properties: KubernetesGroupNodeProperties = KubernetesGroupNodeProperties()
    sub_resource_relationship: KubernetesGroupToClusterRel = (
        KubernetesGroupToClusterRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            KubernetesGroupToOktaGroupRel(),
            KubernetesGroupToAWSRoleRel(),
            KubernetesGroupToAWSUserRel(),
        ]
    )

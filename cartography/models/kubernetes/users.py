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
class KubernetesUserNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id")
    name: PropertyRef = PropertyRef("name")
    cluster_name: PropertyRef = PropertyRef("cluster_name")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class KubernetesUserToClusterRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class KubernetesUserToClusterRel(CartographyRelSchema):
    target_node_label: str = "KubernetesCluster"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("CLUSTER_ID", set_in_kwargs=True)}
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: KubernetesUserToClusterRelProperties = (
        KubernetesUserToClusterRelProperties()
    )


@dataclass(frozen=True)
class KubernetesUserToOktaUserRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class KubernetesUserToAWSRoleRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class KubernetesUserToAWSUserRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class KubernetesUserToOktaUserRel(CartographyRelSchema):
    target_node_label: str = "OktaUser"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"email": PropertyRef("name")}
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "MAPS_TO"
    properties: KubernetesUserToOktaUserRelProperties = (
        KubernetesUserToOktaUserRelProperties()
    )


@dataclass(frozen=True)
class KubernetesUserToAWSRoleRel(CartographyRelSchema):
    target_node_label: str = "AWSRole"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"arn": PropertyRef("aws_role_arn")}
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "MAPS_TO"
    properties: KubernetesUserToAWSRoleRelProperties = (
        KubernetesUserToAWSRoleRelProperties()
    )


@dataclass(frozen=True)
class KubernetesUserToAWSUserRel(CartographyRelSchema):
    target_node_label: str = "AWSUser"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"arn": PropertyRef("aws_user_arn")}
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "MAPS_TO"
    properties: KubernetesUserToAWSUserRelProperties = (
        KubernetesUserToAWSUserRelProperties()
    )


@dataclass(frozen=True)
class KubernetesUserSchema(CartographyNodeSchema):
    label: str = "KubernetesUser"
    properties: KubernetesUserNodeProperties = KubernetesUserNodeProperties()
    sub_resource_relationship: KubernetesUserToClusterRel = KubernetesUserToClusterRel()
    other_relationships: OtherRelationships = OtherRelationships(
        [
            KubernetesUserToOktaUserRel(),
            KubernetesUserToAWSRoleRel(),
            KubernetesUserToAWSUserRel(),
        ]
    )

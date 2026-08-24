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
from cartography.models.ontology.labels import USER_GROUP


@dataclass(frozen=True)
class KubernetesGroupNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id", description="Identifier for the group.")
    name: PropertyRef = PropertyRef("name", description="Name of the Kubernetes group.")
    cluster_name: PropertyRef = PropertyRef(
        "cluster_name", description="Name of the cluster this group belongs to."
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class KubernetesGroupToClusterRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class KubernetesGroupToClusterRel(CartographyRelSchema):
    """Links a cluster to one of its groups."""

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
    """Links an Okta group to the Kubernetes group it maps to."""

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
    """Links an AWS IAM role to the Kubernetes group it maps to."""

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
    """Links an AWS IAM user to the Kubernetes group it maps to."""

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
    "A group identity referenced by Kubernetes RBAC."

    label: str = "KubernetesGroup"
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels([USER_GROUP])
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

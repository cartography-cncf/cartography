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
class KubernetesClusterRoleBindingNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id")
    name: PropertyRef = PropertyRef("name")
    uid: PropertyRef = PropertyRef("uid")
    creation_timestamp: PropertyRef = PropertyRef("creation_timestamp")
    resource_version: PropertyRef = PropertyRef("resource_version")
    role_name: PropertyRef = PropertyRef("role_name")
    role_kind: PropertyRef = PropertyRef("role_kind")
    service_account_ids: PropertyRef = PropertyRef("service_account_ids")
    user_ids: PropertyRef = PropertyRef("user_ids")
    group_ids: PropertyRef = PropertyRef("group_ids")
    role_id: PropertyRef = PropertyRef("role_id")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class KubernetesClusterRoleBindingToClusterRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class KubernetesClusterRoleBindingToClusterRel(CartographyRelSchema):
    target_node_label: str = "KubernetesCluster"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("CLUSTER_ID", set_in_kwargs=True)}
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: KubernetesClusterRoleBindingToClusterRelProperties = (
        KubernetesClusterRoleBindingToClusterRelProperties()
    )


@dataclass(frozen=True)
class KubernetesClusterRoleBindingToServiceAccountRelProperties(
    CartographyRelProperties
):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class KubernetesClusterRoleBindingToServiceAccountRel(CartographyRelSchema):
    target_node_label: str = "KubernetesServiceAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("service_account_ids", one_to_many=True)}
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "SUBJECT"
    properties: KubernetesClusterRoleBindingToServiceAccountRelProperties = (
        KubernetesClusterRoleBindingToServiceAccountRelProperties()
    )


@dataclass(frozen=True)
class KubernetesClusterRoleBindingToClusterRoleRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class KubernetesClusterRoleBindingToClusterRoleRel(CartographyRelSchema):
    target_node_label: str = "KubernetesClusterRole"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("role_id")}
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "ROLE_REF"
    properties: KubernetesClusterRoleBindingToClusterRoleRelProperties = (
        KubernetesClusterRoleBindingToClusterRoleRelProperties()
    )


@dataclass(frozen=True)
class KubernetesClusterRoleBindingToUserRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class KubernetesClusterRoleBindingToUserRel(CartographyRelSchema):
    target_node_label: str = "KubernetesUser"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("user_ids", one_to_many=True)}
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "SUBJECT"
    properties: KubernetesClusterRoleBindingToUserRelProperties = (
        KubernetesClusterRoleBindingToUserRelProperties()
    )


@dataclass(frozen=True)
class KubernetesClusterRoleBindingToGroupRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class KubernetesClusterRoleBindingToGroupRel(CartographyRelSchema):
    target_node_label: str = "KubernetesGroup"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("group_ids", one_to_many=True)}
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "SUBJECT"
    properties: KubernetesClusterRoleBindingToGroupRelProperties = (
        KubernetesClusterRoleBindingToGroupRelProperties()
    )


@dataclass(frozen=True)
class KubernetesClusterRoleBindingSchema(CartographyNodeSchema):
    label: str = "KubernetesClusterRoleBinding"
    properties: KubernetesClusterRoleBindingNodeProperties = (
        KubernetesClusterRoleBindingNodeProperties()
    )
    sub_resource_relationship: KubernetesClusterRoleBindingToClusterRel = (
        KubernetesClusterRoleBindingToClusterRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            KubernetesClusterRoleBindingToServiceAccountRel(),
            KubernetesClusterRoleBindingToUserRel(),
            KubernetesClusterRoleBindingToGroupRel(),
            KubernetesClusterRoleBindingToClusterRoleRel(),
        ]
    )

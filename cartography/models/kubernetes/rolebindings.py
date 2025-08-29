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
class KubernetesRoleBindingNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id")
    name: PropertyRef = PropertyRef("name")
    namespace: PropertyRef = PropertyRef("namespace")
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
class KubernetesRoleBindingToNamespaceRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class KubernetesRoleBindingToNamespaceRel(CartographyRelSchema):
    target_node_label: str = "KubernetesNamespace"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {
            "cluster_name": PropertyRef("CLUSTER_NAME", set_in_kwargs=True),
            "name": PropertyRef("namespace"),
        }
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "CONTAINS"
    properties: KubernetesRoleBindingToNamespaceRelProperties = (
        KubernetesRoleBindingToNamespaceRelProperties()
    )


@dataclass(frozen=True)
class KubernetesRoleBindingToClusterRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class KubernetesRoleBindingToClusterRel(CartographyRelSchema):
    target_node_label: str = "KubernetesCluster"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("CLUSTER_ID", set_in_kwargs=True)}
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: KubernetesRoleBindingToClusterRelProperties = (
        KubernetesRoleBindingToClusterRelProperties()
    )


@dataclass(frozen=True)
class KubernetesRoleBindingToServiceAccountRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class KubernetesRoleBindingToServiceAccountRel(CartographyRelSchema):
    target_node_label: str = "KubernetesServiceAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("service_account_ids", one_to_many=True)}
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "SUBJECT"
    properties: KubernetesRoleBindingToServiceAccountRelProperties = (
        KubernetesRoleBindingToServiceAccountRelProperties()
    )


@dataclass(frozen=True)
class KubernetesRoleBindingToUserRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class KubernetesRoleBindingToUserRel(CartographyRelSchema):
    target_node_label: str = "KubernetesUser"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("user_ids", one_to_many=True)}
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "SUBJECT"
    properties: KubernetesRoleBindingToUserRelProperties = (
        KubernetesRoleBindingToUserRelProperties()
    )


@dataclass(frozen=True)
class KubernetesRoleBindingToGroupRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class KubernetesRoleBindingToGroupRel(CartographyRelSchema):
    target_node_label: str = "KubernetesGroup"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("group_ids", one_to_many=True)}
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "SUBJECT"
    properties: KubernetesRoleBindingToGroupRelProperties = (
        KubernetesRoleBindingToGroupRelProperties()
    )


@dataclass(frozen=True)
class KubernetesRoleBindingToRoleRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class KubernetesRoleBindingToRoleRel(CartographyRelSchema):
    target_node_label: str = "KubernetesRole"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("role_id")}
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "ROLE_REF"
    properties: KubernetesRoleBindingToRoleRelProperties = (
        KubernetesRoleBindingToRoleRelProperties()
    )


@dataclass(frozen=True)
class KubernetesRoleBindingSchema(CartographyNodeSchema):
    label: str = "KubernetesRoleBinding"
    properties: KubernetesRoleBindingNodeProperties = (
        KubernetesRoleBindingNodeProperties()
    )
    sub_resource_relationship: KubernetesRoleBindingToClusterRel = (
        KubernetesRoleBindingToClusterRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            KubernetesRoleBindingToNamespaceRel(),
            KubernetesRoleBindingToServiceAccountRel(),
            KubernetesRoleBindingToUserRel(),
            KubernetesRoleBindingToGroupRel(),
            KubernetesRoleBindingToRoleRel(),
        ]
    )

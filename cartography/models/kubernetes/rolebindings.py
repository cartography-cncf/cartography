from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties, CartographyNodeSchema
from cartography.models.core.relationships import (
    CartographyRelProperties,
    CartographyRelSchema,
    LinkDirection,
    make_target_node_matcher,
    TargetNodeMatcher,
)


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
    subject_name: PropertyRef = PropertyRef("subject_name")
    subject_namespace: PropertyRef = PropertyRef("subject_namespace")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class KubernetesRoleBindingToNamespaceRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class KubernetesRoleBindingToNamespaceRel(CartographyRelSchema):
    target_node_label: str = "KubernetesNamespace"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"name": PropertyRef("namespace")}
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
        {"id": PropertyRef("cluster_id", set_in_kwargs=True)}
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
        {"id": PropertyRef("subject_namespace") + "/" + PropertyRef("subject_name")}
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "SUBJECT"
    properties: KubernetesRoleBindingToServiceAccountRelProperties = (
        KubernetesRoleBindingToServiceAccountRelProperties()
    )


@dataclass(frozen=True)
class KubernetesRoleBindingToRoleRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class KubernetesRoleBindingToRoleRel(CartographyRelSchema):
    target_node_label: str = "KubernetesRole"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("namespace") + "/" + PropertyRef("role_name")}
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "BINDS_ROLE"
    properties: KubernetesRoleBindingToRoleRelProperties = (
        KubernetesRoleBindingToRoleRelProperties()
    )


@dataclass(frozen=True)
class KubernetesRoleBindingSchema(CartographyNodeSchema):
    label: str = "KubernetesRoleBinding"
    properties: KubernetesRoleBindingNodeProperties = KubernetesRoleBindingNodeProperties()
    sub_resource_relationship: KubernetesRoleBindingToClusterRel = KubernetesRoleBindingToClusterRel()
    other_relationships: tuple = (
        KubernetesRoleBindingToNamespaceRel(),
        KubernetesRoleBindingToServiceAccountRel(),
        KubernetesRoleBindingToRoleRel(),
    ) 
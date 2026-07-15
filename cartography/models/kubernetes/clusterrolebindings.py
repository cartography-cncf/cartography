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
    id: PropertyRef = PropertyRef(
        "id",
        description="Identifier for the ClusterRoleBinding derived from cluster_name and name (e.g. `my-cluster/cluster-admin-binding`).",
    )
    name: PropertyRef = PropertyRef(
        "name", description="Name of the Kubernetes ClusterRoleBinding."
    )
    uid: PropertyRef = PropertyRef(
        "uid", description="UID of the Kubernetes ClusterRoleBinding."
    )
    creation_timestamp: PropertyRef = PropertyRef(
        "creation_timestamp",
        description="Timestamp of the creation time of the Kubernetes ClusterRoleBinding.",
    )
    resource_version: PropertyRef = PropertyRef(
        "resource_version",
        description="The resource version of the ClusterRoleBinding for optimistic concurrency control.",
    )
    role_name: PropertyRef = PropertyRef(
        "role_name",
        extra_index=True,
        description="Name of the ClusterRole that this ClusterRoleBinding references.",
    )
    role_kind: PropertyRef = PropertyRef(
        "role_kind", description="Kind of the role reference (typically `ClusterRole`)."
    )
    service_account_ids: PropertyRef = PropertyRef(
        "service_account_ids",
        description="Identifiers of bound service account subjects.",
    )
    user_ids: PropertyRef = PropertyRef(
        "user_ids", description="Identifiers of bound user subjects."
    )
    group_ids: PropertyRef = PropertyRef(
        "group_ids", description="Identifiers of bound group subjects."
    )
    role_id: PropertyRef = PropertyRef(
        "role_id",
        description="Identifier for the target ClusterRole (used for relationship matching).",
    )
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last time the node was updated.",
    )


@dataclass(frozen=True)
class KubernetesClusterRoleBindingToClusterRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class KubernetesClusterRoleBindingToClusterRel(CartographyRelSchema):
    "Links `KubernetesCluster` to `KubernetesClusterRoleBinding` with `RESOURCE`."

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
    "Links `KubernetesClusterRoleBinding` to `KubernetesServiceAccount` with `SUBJECT`."

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
    "Links `KubernetesClusterRoleBinding` to `KubernetesClusterRole` with `ROLE_REF`."

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
    "Links `KubernetesClusterRoleBinding` to `KubernetesUser` with `SUBJECT`."

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
    "Links `KubernetesClusterRoleBinding` to `KubernetesGroup` with `SUBJECT`."

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
    "A cluster-scoped binding between RBAC subjects and a cluster role."

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

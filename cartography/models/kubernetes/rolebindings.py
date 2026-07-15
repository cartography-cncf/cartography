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
    id: PropertyRef = PropertyRef(
        "id",
        description="Identifier for the RoleBinding derived from cluster_name, namespace and name (e.g. `my-cluster/default/my-binding`).",
    )
    name: PropertyRef = PropertyRef(
        "name", description="Name of the Kubernetes RoleBinding."
    )
    namespace: PropertyRef = PropertyRef(
        "namespace",
        description="The Kubernetes namespace where this RoleBinding is deployed.",
    )
    uid: PropertyRef = PropertyRef(
        "uid", description="UID of the Kubernetes RoleBinding."
    )
    creation_timestamp: PropertyRef = PropertyRef(
        "creation_timestamp",
        description="Timestamp of the creation time of the Kubernetes RoleBinding.",
    )
    resource_version: PropertyRef = PropertyRef(
        "resource_version",
        description="The resource version of the RoleBinding for optimistic concurrency control.",
    )
    role_name: PropertyRef = PropertyRef(
        "role_name", description="Name of the Role that this RoleBinding references."
    )
    role_kind: PropertyRef = PropertyRef(
        "role_kind",
        description="Kind of the role reference (e.g. `Role` or `ClusterRole`).",
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
        description="Identifier for the target Role (used for relationship matching).",
    )
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last time the node was updated.",
    )


@dataclass(frozen=True)
class KubernetesRoleBindingToNamespaceRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class KubernetesRoleBindingToNamespaceRel(CartographyRelSchema):
    "Links `KubernetesNamespace` to `KubernetesRoleBinding` with `CONTAINS`."

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
    "Links `KubernetesCluster` to `KubernetesRoleBinding` with `RESOURCE`."

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
    "Links `KubernetesRoleBinding` to `KubernetesServiceAccount` with `SUBJECT`."

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
    "Links `KubernetesRoleBinding` to `KubernetesUser` with `SUBJECT`."

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
    "Links `KubernetesRoleBinding` to `KubernetesGroup` with `SUBJECT`."

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
    "Links `KubernetesRoleBinding` to `KubernetesRole` with `ROLE_REF`."

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
    "A namespace-scoped binding between RBAC subjects and a role."

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

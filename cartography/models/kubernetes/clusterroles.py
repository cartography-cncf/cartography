from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.nodes import ExtraNodeLabels
from cartography.models.core.relationships import CartographyRelProperties
from cartography.models.core.relationships import CartographyRelSchema
from cartography.models.core.relationships import LinkDirection
from cartography.models.core.relationships import make_target_node_matcher
from cartography.models.core.relationships import TargetNodeMatcher


@dataclass(frozen=True)
class KubernetesClusterRoleNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "id",
        description="Identifier for the ClusterRole derived from cluster_name and name (e.g. `my-cluster/cluster-admin`).",
    )
    name: PropertyRef = PropertyRef(
        "name", description="Name of the Kubernetes ClusterRole."
    )
    uid: PropertyRef = PropertyRef(
        "uid", description="UID of the Kubernetes ClusterRole."
    )
    creation_timestamp: PropertyRef = PropertyRef(
        "creation_timestamp",
        description="Timestamp of the creation time of the Kubernetes ClusterRole.",
    )
    resource_version: PropertyRef = PropertyRef(
        "resource_version",
        description="The resource version of the ClusterRole for optimistic concurrency control.",
    )
    api_groups: PropertyRef = PropertyRef(
        "api_groups",
        description='List of API groups that this ClusterRole grants access to (e.g. `["core", "apps"]`).',
    )
    resources: PropertyRef = PropertyRef(
        "resources",
        description='List of resources that this ClusterRole grants access to (e.g. `["pods", "services"]`).',
    )
    verbs: PropertyRef = PropertyRef(
        "verbs",
        description='List of verbs/actions that this ClusterRole allows (e.g. `["get", "list", "create"]`).',
    )
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last time the node was updated.",
    )


@dataclass(frozen=True)
class KubernetesClusterRoleToClusterRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class KubernetesClusterRoleToClusterRel(CartographyRelSchema):
    "Links `KubernetesCluster` to `KubernetesClusterRole` with `RESOURCE`."

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
    "A cluster-scoped Kubernetes RBAC role."

    label: str = "KubernetesClusterRole"
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(["PermissionRole"])
    properties: KubernetesClusterRoleNodeProperties = (
        KubernetesClusterRoleNodeProperties()
    )
    sub_resource_relationship: KubernetesClusterRoleToClusterRel = (
        KubernetesClusterRoleToClusterRel()
    )

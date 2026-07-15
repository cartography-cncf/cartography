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


@dataclass(frozen=True)
class KubernetesRoleNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "id",
        description="Identifier for the Role derived from cluster_name, namespace and name (e.g. `my-cluster/default/pod-reader`).",
    )
    name: PropertyRef = PropertyRef("name", description="Name of the Kubernetes Role.")
    namespace: PropertyRef = PropertyRef(
        "namespace", description="The Kubernetes namespace where this Role is deployed."
    )
    uid: PropertyRef = PropertyRef("uid", description="UID of the Kubernetes Role.")
    creation_timestamp: PropertyRef = PropertyRef(
        "creation_timestamp",
        description="Timestamp of the creation time of the Kubernetes Role.",
    )
    resource_version: PropertyRef = PropertyRef(
        "resource_version",
        description="The resource version of the Role for optimistic concurrency control.",
    )
    api_groups: PropertyRef = PropertyRef(
        "api_groups",
        description='List of API groups that this Role grants access to (e.g. `["core", "apps"]`).',
    )
    resources: PropertyRef = PropertyRef(
        "resources",
        description='List of resources that this Role grants access to (e.g. `["pods", "services"]`).',
    )
    verbs: PropertyRef = PropertyRef(
        "verbs",
        description='List of verbs/actions that this Role allows (e.g. `["get", "list", "create"]`).',
    )
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last time the node was updated.",
    )


@dataclass(frozen=True)
class KubernetesRoleToNamespaceRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class KubernetesRoleToNamespaceRel(CartographyRelSchema):
    "Links `KubernetesNamespace` to `KubernetesRole` with `CONTAINS`."

    target_node_label: str = "KubernetesNamespace"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {
            "cluster_name": PropertyRef("CLUSTER_NAME", set_in_kwargs=True),
            "name": PropertyRef("namespace"),
        }
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "CONTAINS"
    properties: KubernetesRoleToNamespaceRelProperties = (
        KubernetesRoleToNamespaceRelProperties()
    )


@dataclass(frozen=True)
class KubernetesRoleToClusterRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class KubernetesRoleToClusterRel(CartographyRelSchema):
    "Links `KubernetesCluster` to `KubernetesRole` with `RESOURCE`."

    target_node_label: str = "KubernetesCluster"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("CLUSTER_ID", set_in_kwargs=True)}
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: KubernetesRoleToClusterRelProperties = (
        KubernetesRoleToClusterRelProperties()
    )


@dataclass(frozen=True)
class KubernetesRoleSchema(CartographyNodeSchema):
    "A namespace-scoped Kubernetes RBAC role."

    label: str = "KubernetesRole"
    properties: KubernetesRoleNodeProperties = KubernetesRoleNodeProperties()
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(["PermissionRole"])
    sub_resource_relationship: KubernetesRoleToClusterRel = KubernetesRoleToClusterRel()
    other_relationships: OtherRelationships = OtherRelationships(
        [
            KubernetesRoleToNamespaceRel(),
        ]
    )

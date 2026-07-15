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
class KubernetesServiceNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("uid", description="UID of the kubernetes service.")
    name: PropertyRef = PropertyRef(
        "name", extra_index=True, description="Name of the kubernetes service."
    )
    qualified_name: PropertyRef = PropertyRef(
        "qualified_name",
        extra_index=True,
        description="`<namespace>/<name>` identifier used to match the service from cross-namespace references such as `HTTPRoute.spec.rules[].backendRefs`.",
    )
    creation_timestamp: PropertyRef = PropertyRef(
        "creation_timestamp",
        description="Timestamp of the creation time of the kubernetes service.",
    )
    deletion_timestamp: PropertyRef = PropertyRef(
        "deletion_timestamp",
        description="Timestamp of the deletion time of the kubernetes service.",
    )
    namespace: PropertyRef = PropertyRef(
        "namespace",
        extra_index=True,
        description="The Kubernetes namespace where this service is deployed.",
    )
    selector: PropertyRef = PropertyRef(
        "selector",
        description="Labels used by the service to select pods. Fetched from `service.spec.selector`. Stored as a JSON-encoded string.",
    )
    type: PropertyRef = PropertyRef(
        "type",
        extra_index=True,
        description="Type of kubernetes service e.g. `ClusterIP`.",
    )
    cluster_ip: PropertyRef = PropertyRef(
        "cluster_ip",
        description="The internal IP address assigned to the Kubernetes service within the cluster.",
    )
    load_balancer_ip: PropertyRef = PropertyRef(
        "load_balancer_ip",
        description="IP of the load balancer when service type is `LoadBalancer`.",
    )
    load_balancer_ingress: PropertyRef = PropertyRef(
        "load_balancer_ingress",
        description="The list of load balancer ingress points, typically containing the hostname and IP. Stored as a JSON-encoded string.",
    )
    cluster_name: PropertyRef = PropertyRef(
        "CLUSTER_NAME",
        set_in_kwargs=True,
        extra_index=True,
        description="Name of the Kubernetes cluster where this service is deployed.",
    )
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last time the node was updated.",
    )


@dataclass(frozen=True)
class KubernetesServiceToLoadBalancerV2RelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:KubernetesService)-[:USES_LOAD_BALANCER]->(:LoadBalancerV2)
class KubernetesServiceToLoadBalancerV2Rel(CartographyRelSchema):
    "Links `KubernetesService` to `AWSLoadBalancerV2` with `USES_LOAD_BALANCER`."

    target_node_label: str = "AWSLoadBalancerV2"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"dnsname": PropertyRef("load_balancer_dns_names", one_to_many=True)}
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "USES_LOAD_BALANCER"
    properties: KubernetesServiceToLoadBalancerV2RelProperties = (
        KubernetesServiceToLoadBalancerV2RelProperties()
    )


@dataclass(frozen=True)
class KubernetesServiceToKubernetesClusterRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:KubernetesService)<-[:RESOURCE]-(:KubernetesCluster)
class KubernetesServiceToKubernetesClusterRel(CartographyRelSchema):
    "Links `KubernetesCluster` to `KubernetesService` with `RESOURCE`."

    target_node_label: str = "KubernetesCluster"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("CLUSTER_ID", set_in_kwargs=True)}
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: KubernetesServiceToKubernetesClusterRelProperties = (
        KubernetesServiceToKubernetesClusterRelProperties()
    )


@dataclass(frozen=True)
class KubernetesServiceToKubernetesNamespaceRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:KubernetesService)<-[:CONTAINS]-(:KubernetesNamespace)
class KubernetesServiceToKubernetesNamespaceRel(CartographyRelSchema):
    "Links `KubernetesNamespace` to `KubernetesService` with `CONTAINS`."

    target_node_label: str = "KubernetesNamespace"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {
            "cluster_name": PropertyRef("CLUSTER_NAME", set_in_kwargs=True),
            "name": PropertyRef("namespace"),
        }
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "CONTAINS"
    properties: KubernetesServiceToKubernetesNamespaceRelProperties = (
        KubernetesServiceToKubernetesNamespaceRelProperties()
    )


@dataclass(frozen=True)
class KubernetesServiceToKubernetesPodRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:KubernetesService)-[:TARGET]->(:KubernetesPod)
class KubernetesServiceToKubernetesPodRel(CartographyRelSchema):
    "Links `KubernetesService` to `KubernetesPod` with `TARGETS`."

    target_node_label: str = "KubernetesPod"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {
            "cluster_name": PropertyRef("CLUSTER_NAME", set_in_kwargs=True),
            "namespace": PropertyRef("namespace"),
            "id": PropertyRef("pod_ids", one_to_many=True),
        }
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "TARGETS"
    properties: KubernetesServiceToKubernetesPodRelProperties = (
        KubernetesServiceToKubernetesPodRelProperties()
    )


@dataclass(frozen=True)
class KubernetesServiceSchema(CartographyNodeSchema):
    "A Kubernetes service that exposes a set of pods."

    label: str = "KubernetesService"
    properties: KubernetesServiceNodeProperties = KubernetesServiceNodeProperties()
    sub_resource_relationship: KubernetesServiceToKubernetesClusterRel = (
        KubernetesServiceToKubernetesClusterRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            KubernetesServiceToKubernetesNamespaceRel(),
            KubernetesServiceToKubernetesPodRel(),
            KubernetesServiceToLoadBalancerV2Rel(),
        ]
    )

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
class KubernetesIngressNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("uid", description="UID of the Kubernetes Ingress.")
    name: PropertyRef = PropertyRef(
        "name", description="Name of the Kubernetes Ingress."
    )
    namespace: PropertyRef = PropertyRef(
        "namespace",
        extra_index=True,
        description="The Kubernetes namespace where this Ingress is deployed.",
    )
    creation_timestamp: PropertyRef = PropertyRef(
        "creation_timestamp",
        description="Timestamp of the creation time of the Kubernetes Ingress.",
    )
    deletion_timestamp: PropertyRef = PropertyRef(
        "deletion_timestamp",
        description="Timestamp of the deletion time of the Kubernetes Ingress.",
    )
    ingress_class_name: PropertyRef = PropertyRef(
        "ingress_class_name",
        description="The name of the IngressClass cluster resource. Specifies which controller will implement the ingress (e.g. `nginx`, `alb`).",
    )
    rules: PropertyRef = PropertyRef(
        "rules",
        description="The list of host rules used to configure the Ingress. Stored as a JSON-encoded string containing host/path routing rules.",
    )
    annotations: PropertyRef = PropertyRef(
        "annotations",
        description="Annotations on the Ingress resource. Stored as a JSON-encoded string. Contains controller-specific configuration.",
    )
    default_backend: PropertyRef = PropertyRef(
        "default_backend",
        description="A default backend capable of servicing requests that don't match any rule. Stored as a JSON-encoded string.",
    )
    host_names: PropertyRef = PropertyRef(
        "host_names", description="Hostnames configured by the ingress rules."
    )
    cluster_name: PropertyRef = PropertyRef(
        "CLUSTER_NAME",
        set_in_kwargs=True,
        description="Name of the Kubernetes cluster where this Ingress is deployed.",
    )
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last time the node was updated.",
    )
    load_balancer_dns_names: PropertyRef = PropertyRef(
        "load_balancer_dns_names",
        description="List of DNS hostnames from the Ingress status. Used to match to cloud load balancers (e.g., AWS ALB).",
    )
    # AWS Load Balancer Controller group name
    ingress_group_name: PropertyRef = PropertyRef(
        "ingress_group_name",
        extra_index=True,
        description="The ingress group name from the `alb.ingress.kubernetes.io/group.name` annotation (AWS Load Balancer Controller). Allows multiple Ingresses to share a single ALB.",
    )


@dataclass(frozen=True)
class KubernetesIngressToKubernetesClusterRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:KubernetesIngress)<-[:RESOURCE]-(:KubernetesCluster)
class KubernetesIngressToKubernetesClusterRel(CartographyRelSchema):
    "Links `KubernetesCluster` to `KubernetesIngress` with `RESOURCE`."

    target_node_label: str = "KubernetesCluster"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("CLUSTER_ID", set_in_kwargs=True)}
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: KubernetesIngressToKubernetesClusterRelProperties = (
        KubernetesIngressToKubernetesClusterRelProperties()
    )


@dataclass(frozen=True)
class KubernetesIngressToKubernetesNamespaceRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:KubernetesIngress)<-[:CONTAINS]-(:KubernetesNamespace)
class KubernetesIngressToKubernetesNamespaceRel(CartographyRelSchema):
    "Links `KubernetesNamespace` to `KubernetesIngress` with `CONTAINS`."

    target_node_label: str = "KubernetesNamespace"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {
            "cluster_name": PropertyRef("CLUSTER_NAME", set_in_kwargs=True),
            "name": PropertyRef("namespace"),
        }
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "CONTAINS"
    properties: KubernetesIngressToKubernetesNamespaceRelProperties = (
        KubernetesIngressToKubernetesNamespaceRelProperties()
    )


@dataclass(frozen=True)
class KubernetesIngressToKubernetesServiceRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:KubernetesIngress)-[:TARGETS]->(:KubernetesService)
class KubernetesIngressToKubernetesServiceRel(CartographyRelSchema):
    "Links `KubernetesIngress` to `KubernetesService` with `TARGETS`."

    target_node_label: str = "KubernetesService"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {
            "cluster_name": PropertyRef("CLUSTER_NAME", set_in_kwargs=True),
            "namespace": PropertyRef("namespace"),
            "name": PropertyRef("target_services", one_to_many=True),
        }
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "TARGETS"
    properties: KubernetesIngressToKubernetesServiceRelProperties = (
        KubernetesIngressToKubernetesServiceRelProperties()
    )


@dataclass(frozen=True)
class KubernetesIngressToLoadBalancerV2RelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:KubernetesIngress)-[:USES_LOAD_BALANCER]->(:AWSLoadBalancerV2)
class KubernetesIngressToLoadBalancerV2Rel(CartographyRelSchema):
    "Links `KubernetesIngress` to `AWSLoadBalancerV2` with `USES_LOAD_BALANCER`."

    target_node_label: str = "AWSLoadBalancerV2"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"dnsname": PropertyRef("load_balancer_dns_names", one_to_many=True)}
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "USES_LOAD_BALANCER"
    properties: KubernetesIngressToLoadBalancerV2RelProperties = (
        KubernetesIngressToLoadBalancerV2RelProperties()
    )


@dataclass(frozen=True)
class KubernetesIngressSchema(CartographyNodeSchema):
    "A Kubernetes ingress that routes external traffic to services."

    label: str = "KubernetesIngress"
    properties: KubernetesIngressNodeProperties = KubernetesIngressNodeProperties()
    sub_resource_relationship: KubernetesIngressToKubernetesClusterRel = (
        KubernetesIngressToKubernetesClusterRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            KubernetesIngressToKubernetesNamespaceRel(),
            KubernetesIngressToKubernetesServiceRel(),
            KubernetesIngressToLoadBalancerV2Rel(),
        ]
    )

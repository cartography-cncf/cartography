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
class KubernetesEndpointSliceNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("uid", description="UID of the EndpointSlice.")
    name: PropertyRef = PropertyRef("name", description="Name of the EndpointSlice.")
    namespace: PropertyRef = PropertyRef(
        "namespace",
        extra_index=True,
        description="Namespace containing the EndpointSlice.",
    )
    address_type: PropertyRef = PropertyRef(
        "address_type",
        description="Address family used by this slice, such as IPv4 or IPv6.",
    )
    managed_by: PropertyRef = PropertyRef(
        "managed_by",
        description="Controller named by the `endpointslice.kubernetes.io/managed-by` label.",
    )
    service_qualified_name: PropertyRef = PropertyRef(
        "service_qualified_name",
        extra_index=True,
        description="`<namespace>/<name>` of the Service named by the `kubernetes.io/service-name` label.",
    )
    endpoints: PropertyRef = PropertyRef(
        "endpoints",
        description="Endpoint addresses, conditions, topology, and target references as a JSON-encoded list.",
    )
    ports: PropertyRef = PropertyRef(
        "ports",
        description="Ports shared by the endpoints in this slice as a JSON-encoded list.",
    )
    port_numbers: PropertyRef = PropertyRef(
        "port_numbers",
        description="Distinct non-null endpoint port numbers in this slice.",
    )
    port_keys: PropertyRef = PropertyRef(
        "port_keys",
        description="Distinct `<protocol>/<port>` values published by this slice, such as `TCP/8080`.",
    )
    creation_timestamp: PropertyRef = PropertyRef(
        "creation_timestamp",
        description="Timestamp when the EndpointSlice was created.",
    )
    deletion_timestamp: PropertyRef = PropertyRef(
        "deletion_timestamp",
        description="Timestamp when the EndpointSlice was marked for deletion.",
    )
    cluster_name: PropertyRef = PropertyRef(
        "CLUSTER_NAME",
        set_in_kwargs=True,
        extra_index=True,
        description="Name of the Kubernetes cluster containing this EndpointSlice.",
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class KubernetesEndpointSliceRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class KubernetesEndpointSliceToClusterRel(CartographyRelSchema):
    """Links a cluster to one of its EndpointSlices."""

    target_node_label: str = "KubernetesCluster"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("CLUSTER_ID", set_in_kwargs=True)}
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: KubernetesEndpointSliceRelProperties = (
        KubernetesEndpointSliceRelProperties()
    )


@dataclass(frozen=True)
class KubernetesEndpointSliceToNamespaceRel(CartographyRelSchema):
    """Links a namespace to an EndpointSlice it contains."""

    target_node_label: str = "KubernetesNamespace"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {
            "cluster_name": PropertyRef("CLUSTER_NAME", set_in_kwargs=True),
            "name": PropertyRef("namespace"),
        }
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "CONTAINS"
    properties: KubernetesEndpointSliceRelProperties = (
        KubernetesEndpointSliceRelProperties()
    )


@dataclass(frozen=True)
class KubernetesEndpointSliceToServiceRel(CartographyRelSchema):
    """Links an EndpointSlice to the Service named by its service-name label."""

    target_node_label: str = "KubernetesService"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {
            "cluster_name": PropertyRef("CLUSTER_NAME", set_in_kwargs=True),
            "qualified_name": PropertyRef("service_qualified_name"),
        }
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "FOR_SERVICE"
    properties: KubernetesEndpointSliceRelProperties = (
        KubernetesEndpointSliceRelProperties()
    )


@dataclass(frozen=True)
class KubernetesEndpointSliceToPodRel(CartographyRelSchema):
    """Links an EndpointSlice to ready Pod endpoints referenced by the slice."""

    target_node_label: str = "KubernetesPod"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {
            "cluster_name": PropertyRef("CLUSTER_NAME", set_in_kwargs=True),
            "id": PropertyRef("ready_pod_ids", one_to_many=True),
        }
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "TARGETS"
    properties: KubernetesEndpointSliceRelProperties = (
        KubernetesEndpointSliceRelProperties()
    )


@dataclass(frozen=True)
class KubernetesEndpointSliceSchema(CartographyNodeSchema):
    """A Kubernetes EndpointSlice containing a subset of Service backends."""

    label: str = "KubernetesEndpointSlice"
    properties: KubernetesEndpointSliceNodeProperties = (
        KubernetesEndpointSliceNodeProperties()
    )
    sub_resource_relationship: KubernetesEndpointSliceToClusterRel = (
        KubernetesEndpointSliceToClusterRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            KubernetesEndpointSliceToNamespaceRel(),
            KubernetesEndpointSliceToServiceRel(),
            KubernetesEndpointSliceToPodRel(),
        ]
    )

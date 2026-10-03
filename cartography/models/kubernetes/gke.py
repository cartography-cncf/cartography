"""Cross-provider relationships derived from GKE and Kubernetes inventory."""

from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.relationships import CartographyRelProperties
from cartography.models.core.relationships import CartographyRelSchema
from cartography.models.core.relationships import LinkDirection
from cartography.models.core.relationships import make_source_node_matcher
from cartography.models.core.relationships import make_target_node_matcher
from cartography.models.core.relationships import SourceNodeMatcher
from cartography.models.core.relationships import TargetNodeMatcher


@dataclass(frozen=True)
class GKEBridgeMatchLinkProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    _sub_resource_label: PropertyRef = PropertyRef(
        "_sub_resource_label", set_in_kwargs=True
    )
    _sub_resource_id: PropertyRef = PropertyRef("_sub_resource_id", set_in_kwargs=True)


@dataclass(frozen=True)
class GKEClusterMatchLink(CartographyRelSchema):
    """Maps a cloud cluster to its Kubernetes API inventory, scoped to the cloud resource."""

    source_node_label: str = "GKECluster"
    source_node_matcher: SourceNodeMatcher = make_source_node_matcher(
        {"id": PropertyRef("source_id")}
    )
    target_node_label: str = "KubernetesCluster"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("target_id")}
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "MAPS_TO"
    properties: GKEBridgeMatchLinkProperties = GKEBridgeMatchLinkProperties()


@dataclass(frozen=True)
class GKENodePoolMatchLink(GKEClusterMatchLink):
    """Maps a registered node to the GKE node pool named in its labels."""

    source_node_label: str = "KubernetesNode"
    target_node_label: str = "GKENodePool"
    rel_label: str = "MEMBER_OF"


@dataclass(frozen=True)
class GKEPoolMatchLink(GKEClusterMatchLink):
    """Identifies the Google-managed workload pool configured on a cluster."""

    target_node_label: str = "GCPWorkloadIdentityPool"
    rel_label: str = "USES_WORKLOAD_IDENTITY_POOL"


@dataclass(frozen=True)
class GKEPolicyEvidenceMatchLinkProperties(GKEBridgeMatchLinkProperties):
    matched_members: PropertyRef = PropertyRef(
        "matched_members",
        description="Exact IAM members matching this Kubernetes identity.",
    )
    policy_lastupdated: PropertyRef = PropertyRef(
        "policy_lastupdated",
        description="Timestamp of the IAM policy snapshot used for this relationship.",
    )


@dataclass(frozen=True)
class GKEWorkloadPolicyMatchLink(GKEClusterMatchLink):
    """Matches a KSA to an IAM allow binding; conditions remain on the binding and are not evaluated."""

    source_node_label: str = "KubernetesServiceAccount"
    target_node_label: str = "GCPPolicyBinding"
    rel_label: str = "HAS_ALLOW_POLICY"
    properties: GKEPolicyEvidenceMatchLinkProperties = (
        GKEPolicyEvidenceMatchLinkProperties()
    )


@dataclass(frozen=True)
class GKEWorkloadImpersonationMatchLink(GKEWorkloadPolicyMatchLink):
    """Links an annotated KSA to a GSA with an unconditional workloadIdentityUser grant. Runtime access also depends on GKE configuration and other policy controls."""

    target_node_label: str = "GCPServiceAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"email": PropertyRef("target_id")}
    )
    rel_label: str = "WORKLOAD_IDENTITY_BINDING"


@dataclass(frozen=True)
class GKEUserMatchLink(GKEClusterMatchLink):
    """Maps an inventoried Google principal email to an exact Kubernetes RBAC User subject."""

    source_node_label: str = "GCPPrincipal"
    source_node_matcher: SourceNodeMatcher = make_source_node_matcher(
        {"email": PropertyRef("source_id")}
    )
    target_node_label: str = "KubernetesUser"


@dataclass(frozen=True)
class GKEServiceLoadBalancerMatchLink(GKEClusterMatchLink):
    """Correlates a Service status address with a project and network scoped GCP forwarding rule."""

    source_node_label: str = "KubernetesService"
    target_node_label: str = "GCPForwardingRule"
    rel_label: str = "USES_LOAD_BALANCER"


@dataclass(frozen=True)
class GKEIngressLoadBalancerMatchLink(GKEServiceLoadBalancerMatchLink):
    """Correlates an Ingress status address with a scoped GCP forwarding rule."""

    source_node_label: str = "KubernetesIngress"


@dataclass(frozen=True)
class GKEGatewayLoadBalancerMatchLink(GKEServiceLoadBalancerMatchLink):
    """Correlates a Gateway status address with a scoped GCP forwarding rule."""

    source_node_label: str = "KubernetesGateway"

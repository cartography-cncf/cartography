from cartography.rules.spec.model import Fact
from cartography.rules.spec.model import Finding
from cartography.rules.spec.model import Maturity
from cartography.rules.spec.model import Module
from cartography.rules.spec.model import Rule

# AWS Fact
_aws_eks_control_plane_exposed = Fact(
    id="aws_eks_control_plane_exposed",
    name="Internet-Exposed EKS Control Plane",
    description=(
        "EKS clusters whose Kubernetes API server is reachable from the "
        "public internet. The ontology normalizes "
        "EKSCluster.endpoint_public_access into "
        "_ont_control_plane_public_access, and the AWS EKS asset-exposure "
        "analysis job further marks the cluster with exposed_internet=true. "
        "Both conditions are required to keep parity with the existing "
        "aws_eks_asset_exposure semantics. Note: clusters restricted via "
        "public-access CIDRs still match, mirroring the AWS console "
        "'Public' endpoint mode."
    ),
    cypher_query="""
    MATCH (c:EKSCluster)
    WHERE c._ont_control_plane_public_access = true
      AND c.exposed_internet = true
    RETURN
        c.id AS id,
        c.name AS name,
        c.region AS region,
        c.version AS version,
        'aws' AS cloud
    """,
    cypher_visual_query="""
    MATCH p=(acc:AWSAccount)-[:RESOURCE]->(c:EKSCluster)
    WHERE c._ont_control_plane_public_access = true
      AND c.exposed_internet = true
    RETURN *
    """,
    cypher_count_query="""
    MATCH (c:EKSCluster)
    RETURN COUNT(c) AS count
    """,
    asset_id_field="id",
    module=Module.AWS,
    maturity=Maturity.EXPERIMENTAL,
)


# GCP Fact
_gcp_gke_control_plane_exposed = Fact(
    id="gcp_gke_control_plane_exposed",
    name="Internet-Exposed GKE Control Plane",
    description=(
        "GKE clusters whose Kubernetes API server is reachable from the "
        "public internet. Derived from "
        "privateClusterConfig.enablePrivateEndpoint: when false (or the "
        "cluster is not configured as a private cluster at all), the "
        "master endpoint is publicly reachable. Note: clusters restricted "
        "via masterAuthorizedNetworksConfig still match, mirroring the AWS "
        "EKS convention."
    ),
    cypher_query="""
    MATCH (c:GKECluster)
    WHERE c._ont_control_plane_public_access = true
    RETURN
        c.id AS id,
        c.name AS name,
        c.location AS region,
        c.current_master_version AS version,
        'gcp' AS cloud
    """,
    cypher_visual_query="""
    MATCH p=(proj:GCPProject)-[:RESOURCE]->(c:GKECluster)
    WHERE c._ont_control_plane_public_access = true
    RETURN *
    """,
    cypher_count_query="""
    MATCH (c:GKECluster)
    RETURN COUNT(c) AS count
    """,
    asset_id_field="id",
    module=Module.GCP,
    maturity=Maturity.EXPERIMENTAL,
)


# Azure Fact
_azure_aks_control_plane_exposed = Fact(
    id="azure_aks_control_plane_exposed",
    name="Internet-Exposed AKS Control Plane",
    description=(
        "AKS clusters whose Kubernetes API server is reachable from the "
        "public internet. Derived from two independent knobs that each "
        "close the public path: apiServerAccessProfile.enablePrivateCluster "
        "(classic private cluster) and publicNetworkAccess=Disabled (used "
        "by API Server VNet Integration). The cluster is flagged only when "
        "neither knob disables public access. Note: clusters restricted "
        "via authorizedIpRanges still match, mirroring the AWS EKS "
        "convention."
    ),
    cypher_query="""
    MATCH (c:AzureKubernetesCluster)
    WHERE c._ont_control_plane_public_access = true
    RETURN
        c.id AS id,
        c.name AS name,
        c.location AS region,
        c.kubernetes_version AS version,
        'azure' AS cloud
    """,
    cypher_visual_query="""
    MATCH p=(sub:AzureSubscription)-[:RESOURCE]->(c:AzureKubernetesCluster)
    WHERE c._ont_control_plane_public_access = true
    RETURN *
    """,
    cypher_count_query="""
    MATCH (c:AzureKubernetesCluster)
    RETURN COUNT(c) AS count
    """,
    asset_id_field="id",
    module=Module.AZURE,
    maturity=Maturity.EXPERIMENTAL,
)


# TODO: wire CIS Framework references once CIS EKS / GKE / AKS benchmarks are
# adopted repo-wide. The relevant controls are CIS Amazon EKS Benchmark 5.4.2,
# CIS Google Kubernetes Engine (GKE) Benchmark 5.6.4, and CIS Microsoft Azure
# Kubernetes Service (AKS) Benchmark 5.4.2. Adding the Framework entries here
# without the corresponding benchmark coverage elsewhere would introduce
# orphan scopes ("eks", "gke", "aks") that no other rule maps to.


# Rule
class KubernetesControlPlaneExposed(Finding):
    id: str | None = None
    name: str | None = None
    region: str | None = None
    version: str | None = None
    cloud: str | None = None


kubernetes_control_plane_exposed = Rule(
    id="kubernetes_control_plane_exposed",
    name="Internet-Exposed Kubernetes Control Plane",
    description=(
        "Managed Kubernetes clusters whose API server is reachable from "
        "the public internet. Covers AWS EKS, GCP GKE, and Azure AKS. "
        "Aligns with CIS Amazon EKS Benchmark 5.4.2, CIS GKE Benchmark "
        "5.6.4, and CIS AKS Benchmark 5.4.2; Framework wiring is pending "
        "until those benchmarks are added repo-wide."
    ),
    output_model=KubernetesControlPlaneExposed,
    facts=(
        _aws_eks_control_plane_exposed,
        _gcp_gke_control_plane_exposed,
        _azure_aks_control_plane_exposed,
    ),
    tags=(
        "infrastructure",
        "kubernetes",
        "attack_surface",
        "stride:tampering",
        "stride:elevation_of_privilege",
    ),
    version="0.1.0",
)

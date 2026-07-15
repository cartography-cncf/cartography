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
class KubernetesClusterNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "id",
        description="Identifier for the cluster i.e. UID of `kube-system` namespace.",
    )
    name: PropertyRef = PropertyRef(
        "name",
        extra_index=True,
        description="Name assigned to the cluster which is derived from kubeconfig context.",
    )
    creation_timestamp: PropertyRef = PropertyRef(
        "creation_timestamp",
        description="Timestamp of when the cluster was created i.e. creation of `kube-system` namespace.",
    )
    external_id: PropertyRef = PropertyRef(
        "external_id",
        extra_index=True,
        description="Identifier for the cluster fetched from the kubeconfig context. For EKS clusters this should be the `arn`.",
    )
    version: PropertyRef = PropertyRef(
        "git_version",
        description="Git version of the Kubernetes cluster (e.g. v1.27.3).",
    )
    version_major: PropertyRef = PropertyRef(
        "version_major",
        description="Major version number of the Kubernetes cluster (e.g. 1).",
    )
    version_minor: PropertyRef = PropertyRef(
        "version_minor",
        description="Minor version number of the Kubernetes cluster (e.g. 27).",
    )
    go_version: PropertyRef = PropertyRef(
        "go_version",
        description="Version of Go used to compile Kubernetes (e.g. go1.20.5).",
    )
    compiler: PropertyRef = PropertyRef(
        "compiler", description="Compiler used to build Kubernetes (e.g. gc)."
    )
    platform: PropertyRef = PropertyRef(
        "platform",
        description="Operating system and architecture the cluster is running on (e.g. linux/amd64).",
    )
    api_server_url: PropertyRef = PropertyRef(
        "api_server_url", description="Kubernetes API server URL from kubeconfig."
    )
    kubeconfig_insecure_skip_tls_verify: PropertyRef = PropertyRef(
        "kubeconfig_insecure_skip_tls_verify",
        description="Whether kubeconfig is configured to skip API server TLS verification.",
    )
    kubeconfig_has_certificate_authority_data: PropertyRef = PropertyRef(
        "kubeconfig_has_certificate_authority_data",
        description="True when kubeconfig has inline `certificate-authority-data` for this cluster.",
    )
    kubeconfig_has_certificate_authority_file: PropertyRef = PropertyRef(
        "kubeconfig_has_certificate_authority_file",
        description="True when kubeconfig has a `certificate-authority` file path for this cluster.",
    )
    kubeconfig_ca_file_path: PropertyRef = PropertyRef(
        "kubeconfig_ca_file_path",
        description="CA file path from kubeconfig when `certificate-authority` is configured.",
    )
    kubeconfig_has_client_certificate: PropertyRef = PropertyRef(
        "kubeconfig_has_client_certificate",
        description="True when kubeconfig user has a client cert (`client-certificate` or `client-certificate-data`).",
    )
    kubeconfig_has_client_key: PropertyRef = PropertyRef(
        "kubeconfig_has_client_key",
        description="True when kubeconfig user has a client key (`client-key` or `client-key-data`).",
    )
    kubeconfig_tls_configuration_status: PropertyRef = PropertyRef(
        "kubeconfig_tls_configuration_status",
        description="Derived kubeconfig TLS posture (`valid_config`, `insecure_skip_tls`, `missing_ca_material`, `unknown`).",
    )
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last time the node was updated.",
    )


@dataclass(frozen=True)
class KubernetesClusterToEKSClusterRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:AWSEKSCluster)-[:MAPS_TO]->(:KubernetesCluster)
class KubernetesClusterToEKSClusterRel(CartographyRelSchema):
    "Links `AWSEKSCluster` to `KubernetesCluster` with `MAPS_TO`."

    target_node_label: str = "AWSEKSCluster"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"arn": PropertyRef("external_id")}
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "MAPS_TO"
    properties: KubernetesClusterToEKSClusterRelProperties = (
        KubernetesClusterToEKSClusterRelProperties()
    )


@dataclass(frozen=True)
class KubernetesClusterSchema(CartographyNodeSchema):
    "A Kubernetes cluster discovered from a kubeconfig context."

    label: str = "KubernetesCluster"
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(["ComputeCluster"])
    properties: KubernetesClusterNodeProperties = KubernetesClusterNodeProperties()
    other_relationships: OtherRelationships = OtherRelationships(
        [KubernetesClusterToEKSClusterRel()]
    )

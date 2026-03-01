from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema


@dataclass(frozen=True)
class KubernetesClusterNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id")
    name: PropertyRef = PropertyRef("name", extra_index=True)
    creation_timestamp: PropertyRef = PropertyRef("creation_timestamp")
    external_id: PropertyRef = PropertyRef("external_id", extra_index=True)
    version: PropertyRef = PropertyRef("git_version")
    version_major: PropertyRef = PropertyRef("version_major")
    version_minor: PropertyRef = PropertyRef("version_minor")
    go_version: PropertyRef = PropertyRef("go_version")
    compiler: PropertyRef = PropertyRef("compiler")
    platform: PropertyRef = PropertyRef("platform")
    api_server_url: PropertyRef = PropertyRef("api_server_url")
    kubeconfig_insecure_skip_tls_verify: PropertyRef = PropertyRef(
        "kubeconfig_insecure_skip_tls_verify",
    )
    kubeconfig_has_certificate_authority_data: PropertyRef = PropertyRef(
        "kubeconfig_has_certificate_authority_data",
    )
    kubeconfig_has_certificate_authority_file: PropertyRef = PropertyRef(
        "kubeconfig_has_certificate_authority_file",
    )
    kubeconfig_ca_file_path: PropertyRef = PropertyRef("kubeconfig_ca_file_path")
    kubeconfig_has_client_certificate: PropertyRef = PropertyRef(
        "kubeconfig_has_client_certificate",
    )
    kubeconfig_has_client_key: PropertyRef = PropertyRef("kubeconfig_has_client_key")
    kubeconfig_tls_configuration_status: PropertyRef = PropertyRef(
        "kubeconfig_tls_configuration_status",
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class KubernetesClusterSchema(CartographyNodeSchema):
    label: str = "KubernetesCluster"
    properties: KubernetesClusterNodeProperties = KubernetesClusterNodeProperties()

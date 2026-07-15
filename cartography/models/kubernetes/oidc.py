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
class KubernetesOIDCProviderNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "id",
        description="Identifier for the OIDC Provider derived from cluster name and provider name (e.g. `my-cluster/oidc/auth0-provider`).",
    )
    issuer_url: PropertyRef = PropertyRef(
        "issuer_url",
        description="URL of the OIDC issuer (e.g. `https://company.auth0.com/`).",
    )
    cluster_name: PropertyRef = PropertyRef(
        "cluster_name",
        description="Name of the Kubernetes cluster this provider is associated with.",
    )
    k8s_platform: PropertyRef = PropertyRef(
        "k8s_platform",
        description="Type of Kubernetes platform managing this OIDC configuration (e.g. `eks` for AWS EKS, `aks` for Azure AKS).",
    )
    client_id: PropertyRef = PropertyRef(
        "client_id", description="OIDC client ID used for authentication."
    )
    status: PropertyRef = PropertyRef(
        "status",
        description="Status of the OIDC provider configuration (e.g. `ACTIVE`).",
    )
    name: PropertyRef = PropertyRef(
        "name", description="Name of the OIDC provider configuration."
    )
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last time the node was updated.",
    )


@dataclass(frozen=True)
class KubernetesOIDCProviderToClusterRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class KubernetesOIDCProviderToClusterRel(CartographyRelSchema):
    "Links `KubernetesCluster` to `KubernetesOIDCProvider` with `RESOURCE`."

    target_node_label: str = "KubernetesCluster"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("CLUSTER_ID", set_in_kwargs=True)}
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: KubernetesOIDCProviderToClusterRelProperties = (
        KubernetesOIDCProviderToClusterRelProperties()
    )


@dataclass(frozen=True)
class KubernetesOIDCProviderTrustsClusterRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class KubernetesOIDCProviderTrustsClusterRel(CartographyRelSchema):
    "Links `KubernetesCluster` to `KubernetesOIDCProvider` with `TRUSTS`."

    target_node_label: str = "KubernetesCluster"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("CLUSTER_ID", set_in_kwargs=True)}
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "TRUSTS"
    properties: KubernetesOIDCProviderTrustsClusterRelProperties = (
        KubernetesOIDCProviderTrustsClusterRelProperties()
    )


@dataclass(frozen=True)
class KubernetesOIDCProviderSchema(CartographyNodeSchema):
    "An external OIDC identity provider trusted by a Kubernetes cluster."

    label: str = "KubernetesOIDCProvider"
    properties: KubernetesOIDCProviderNodeProperties = (
        KubernetesOIDCProviderNodeProperties()
    )
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(["IdentityProvider"])
    sub_resource_relationship: KubernetesOIDCProviderToClusterRel = (
        KubernetesOIDCProviderToClusterRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [KubernetesOIDCProviderTrustsClusterRel()]
    )

from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.relationships import CartographyRelProperties
from cartography.models.core.relationships import CartographyRelSchema
from cartography.models.core.relationships import LinkDirection
from cartography.models.core.relationships import make_target_node_matcher
from cartography.models.core.relationships import TargetNodeMatcher


@dataclass(frozen=True)
class KubernetesOIDCProviderNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id")
    issuer_url: PropertyRef = PropertyRef("issuer_url")
    cluster_name: PropertyRef = PropertyRef("cluster_name")
    k8s_platform: PropertyRef = PropertyRef("k8s_platform")
    client_id: PropertyRef = PropertyRef("client_id")
    status: PropertyRef = PropertyRef("status")
    name: PropertyRef = PropertyRef("name")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class KubernetesOIDCProviderToClusterRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class KubernetesOIDCProviderToClusterRel(CartographyRelSchema):
    target_node_label: str = "KubernetesCluster"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("CLUSTER_ID", set_in_kwargs=True)}
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "TRUSTS"
    properties: KubernetesOIDCProviderToClusterRelProperties = (
        KubernetesOIDCProviderToClusterRelProperties()
    )


@dataclass(frozen=True)
class KubernetesOIDCProviderSchema(CartographyNodeSchema):
    label: str = "KubernetesOIDCProvider"
    properties: KubernetesOIDCProviderNodeProperties = (
        KubernetesOIDCProviderNodeProperties()
    )
    sub_resource_relationship: KubernetesOIDCProviderToClusterRel = (
        KubernetesOIDCProviderToClusterRel()
    )

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
    """
    Sub-resource relationship: (KubernetesCluster)-[:RESOURCE]->(KubernetesOIDCProvider).

    Provider IDs are constructed as `{cluster_name}/oidc/{provider_name}`, so
    in practice each provider is 1:1 with its owning cluster and the standard
    `RESOURCE` cleanup scope is safe.
    """

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
    """
    Semantic relationship: (KubernetesCluster)-[:TRUSTS]->(KubernetesOIDCProvider).

    Preserved alongside the cleanup-oriented `RESOURCE` edge so that analysis
    queries can keep matching on the more meaningful `TRUSTS` predicate.
    """

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

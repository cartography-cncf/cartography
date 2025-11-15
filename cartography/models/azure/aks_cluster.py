import logging
from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.relationships import CartographyRelProperties
from cartography.models.core.relationships import CartographyRelSchema
from cartography.models.core.relationships import LinkDirection
from cartography.models.core.relationships import make_target_node_matcher
from cartography.models.core.relationships import TargetNodeMatcher

logger = logging.getLogger(__name__)


# --- Node Definitions ---
@dataclass(frozen=True)
class AzureKubernetesClusterProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id")
    name: PropertyRef = PropertyRef("name")
    location: PropertyRef = PropertyRef("location")
    provisioning_state: PropertyRef = PropertyRef("provisioning_state")
    kubernetes_version: PropertyRef = PropertyRef("kubernetes_version")
    fqdn: PropertyRef = PropertyRef("fqdn")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


# --- Relationship Definitions ---
@dataclass(frozen=True)
class AzureKubernetesClusterToSubscriptionRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AzureKubernetesClusterToSubscriptionRel(CartographyRelSchema):
    target_node_label: str = "AzureSubscription"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("AZURE_SUBSCRIPTION_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: AzureKubernetesClusterToSubscriptionRelProperties = (
        AzureKubernetesClusterToSubscriptionRelProperties()
    )


# --- Main Schema ---
@dataclass(frozen=True)
class AzureKubernetesClusterSchema(CartographyNodeSchema):
    label: str = "AzureKubernetesCluster"
    properties: AzureKubernetesClusterProperties = AzureKubernetesClusterProperties()
    sub_resource_relationship: AzureKubernetesClusterToSubscriptionRel = (
        AzureKubernetesClusterToSubscriptionRel()
    )

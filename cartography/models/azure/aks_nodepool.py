import logging
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

logger = logging.getLogger(__name__)


# --- Node Definitions ---
@dataclass(frozen=True)
class AzureKubernetesNodePoolProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id")
    name: PropertyRef = PropertyRef("name")
    provisioning_state: PropertyRef = PropertyRef("provisioning_state")
    vm_size: PropertyRef = PropertyRef("vm_size")
    os_type: PropertyRef = PropertyRef("os_type")
    count: PropertyRef = PropertyRef("count")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


# --- Relationship Definitions ---
@dataclass(frozen=True)
class AzureKubernetesAgentPoolToClusterRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AzureKubernetesAgentPoolToClusterRel(CartographyRelSchema):
    target_node_label: str = "AzureKubernetesCluster"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("CLUSTER_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "HAS_AGENT_POOL"
    properties: AzureKubernetesAgentPoolToClusterRelProperties = (
        AzureKubernetesAgentPoolToClusterRelProperties()
    )


@dataclass(frozen=True)
class AzureKubernetesAgentPoolToSubscriptionRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AzureKubernetesAgentPoolToSubscriptionRel(CartographyRelSchema):
    target_node_label: str = "AzureSubscription"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("AZURE_SUBSCRIPTION_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: AzureKubernetesAgentPoolToSubscriptionRelProperties = (
        AzureKubernetesAgentPoolToSubscriptionRelProperties()
    )


# --- Main Schema ---
@dataclass(frozen=True)
class AzureKubernetesNodePoolSchema(CartographyNodeSchema):
    label: str = "AzureKubernetesAgentPool"
    properties: AzureKubernetesNodePoolProperties = AzureKubernetesNodePoolProperties()
    other_relationships: OtherRelationships = OtherRelationships(
        rels=[
            AzureKubernetesAgentPoolToClusterRel(),
        ],
    )
    sub_resource_relationship: AzureKubernetesAgentPoolToSubscriptionRel = (
        AzureKubernetesAgentPoolToSubscriptionRel()
    )

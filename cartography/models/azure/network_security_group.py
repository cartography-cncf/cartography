import logging
from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.nodes import ExtraNodeLabels
from cartography.models.core.relationships import CartographyRelProperties
from cartography.models.core.relationships import CartographyRelSchema
from cartography.models.core.relationships import LinkDirection
from cartography.models.core.relationships import make_target_node_matcher
from cartography.models.core.relationships import TargetNodeMatcher
from cartography.models.ontology.labels import NETWORK_ACCESS_CONTROL

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class AzureNetworkSecurityGroupProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "id", description="Full Azure resource ID of the network security group."
    )
    name: PropertyRef = PropertyRef(
        "name", description="Name of the network security group."
    )
    location: PropertyRef = PropertyRef(
        "location",
        description="Azure region where the network security group is deployed.",
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AzureNetworkSecurityGroupToSubscriptionRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AzureNetworkSecurityGroupToSubscriptionRel(CartographyRelSchema):
    """An Azure subscription contains the network security group as a resource."""

    target_node_label: str = "AzureSubscription"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("AZURE_SUBSCRIPTION_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: AzureNetworkSecurityGroupToSubscriptionRelProperties = (
        AzureNetworkSecurityGroupToSubscriptionRelProperties()
    )


@dataclass(frozen=True)
class AzureNetworkSecurityGroupSchema(CartographyNodeSchema):
    """An Azure network security group that filters network traffic."""

    label: str = "AzureNetworkSecurityGroup"
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels([NETWORK_ACCESS_CONTROL])
    properties: AzureNetworkSecurityGroupProperties = (
        AzureNetworkSecurityGroupProperties()
    )
    sub_resource_relationship: AzureNetworkSecurityGroupToSubscriptionRel = (
        AzureNetworkSecurityGroupToSubscriptionRel()
    )

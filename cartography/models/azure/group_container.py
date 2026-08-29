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
from cartography.models.core.relationships import OtherRelationships
from cartography.models.core.relationships import TargetNodeMatcher
from cartography.models.ontology.labels import COMPUTE_POD

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class AzureGroupContainerNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "id",
        description="Azure Resource Manager ID of the container group.",
    )
    name: PropertyRef = PropertyRef(
        "name",
        description="Name of the container group.",
    )
    location: PropertyRef = PropertyRef(
        "location",
        description="Azure region where the container group runs.",
    )
    type: PropertyRef = PropertyRef(
        "type",
        description="Azure resource type of the container group.",
    )
    provisioning_state: PropertyRef = PropertyRef(
        "provisioning_state",
        description="Current provisioning state of the container group.",
    )
    ip_address: PropertyRef = PropertyRef(
        "ip_address",
        description="IP address assigned to the container group.",
    )
    ip_address_type: PropertyRef = PropertyRef(
        "ip_address_type",
        description="Exposure type of the container group's IP address.",
    )
    os_type: PropertyRef = PropertyRef(
        "os_type",
        description="Operating system type used by the container group.",
    )
    exposed_internet: PropertyRef = PropertyRef(
        "exposed_internet",
        extra_index=True,
        description="`True` when the container group has a public IP address, or an IP with no subnet attachment. `False` otherwise.",
    )  # Populated by the AZURE_COMPUTE_ASSET_EXPOSURE_CONTAINER analysis job.
    exposed_internet_type: PropertyRef = PropertyRef(
        "exposed_internet_type",
        extra_index=True,
        description="How it is exposed. Always `direct`.",
    )  # Populated by the AZURE_COMPUTE_ASSET_EXPOSURE_CONTAINER analysis job.
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AzureGroupContainerToSubscriptionRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AzureGroupContainerToSubscriptionRel(CartographyRelSchema):
    """An Azure subscription contains the container group as a resource."""

    target_node_label: str = "AzureSubscription"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("AZURE_SUBSCRIPTION_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: AzureGroupContainerToSubscriptionRelProperties = (
        AzureGroupContainerToSubscriptionRelProperties()
    )


@dataclass(frozen=True)
class AzureGroupContainerToSubnetRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AzureGroupContainerToSubnetRel(CartographyRelSchema):
    """An Azure container group is attached to a virtual network subnet."""

    target_node_label: str = "AzureSubnet"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("SUBNET_IDS", one_to_many=True)},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "ATTACHED_TO"
    properties: AzureGroupContainerToSubnetRelProperties = (
        AzureGroupContainerToSubnetRelProperties()
    )


@dataclass(frozen=True)
class AzureGroupContainerSchema(CartographyNodeSchema):
    """An Azure Container Instances container group."""

    label: str = "AzureGroupContainer"
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels([COMPUTE_POD])
    properties: AzureGroupContainerNodeProperties = AzureGroupContainerNodeProperties()
    sub_resource_relationship: AzureGroupContainerToSubscriptionRel = (
        AzureGroupContainerToSubscriptionRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            AzureGroupContainerToSubnetRel(),
        ],
    )

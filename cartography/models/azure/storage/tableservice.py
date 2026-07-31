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


@dataclass(frozen=True)
class AzureStorageTableServiceProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id", description="Azure resource ID.")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    type: PropertyRef = PropertyRef("type", description="Azure resource type.")
    name: PropertyRef = PropertyRef("name", description="Azure resource name.")


@dataclass(frozen=True)
class AzureStorageTableServiceToStorageAccountRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:AzureStorageAccount)-[:USES]->(:AzureStorageTableService)
class AzureStorageTableServiceToStorageAccountRel(CartographyRelSchema):
    """An Azure Storage account uses the table service."""

    target_node_label: str = "AzureStorageAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("storage_account_id")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "USES"
    properties: AzureStorageTableServiceToStorageAccountRelProperties = (
        AzureStorageTableServiceToStorageAccountRelProperties()
    )


@dataclass(frozen=True)
class AzureStorageTableServiceToSubscriptionRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:AzureSubscription)-[:RESOURCE]->(:AzureStorageTableService)
class AzureStorageTableServiceToSubscriptionRel(CartographyRelSchema):
    """An Azure subscription contains the table service as a resource."""

    target_node_label: str = "AzureSubscription"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("AZURE_SUBSCRIPTION_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: AzureStorageTableServiceToSubscriptionRelProperties = (
        AzureStorageTableServiceToSubscriptionRelProperties()
    )


@dataclass(frozen=True)
class AzureStorageTableServiceSchema(CartographyNodeSchema):
    """The Table Storage service of an Azure Storage account."""

    label: str = "AzureStorageTableService"
    properties: AzureStorageTableServiceProperties = (
        AzureStorageTableServiceProperties()
    )
    sub_resource_relationship: AzureStorageTableServiceToSubscriptionRel = (
        AzureStorageTableServiceToSubscriptionRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            AzureStorageTableServiceToStorageAccountRel(),
        ]
    )

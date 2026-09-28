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
class AzureStorageTableProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id", description="Azure resource ID.")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    type: PropertyRef = PropertyRef("type", description="Azure resource type.")
    name: PropertyRef = PropertyRef("name", description="Azure resource name.")
    tablename: PropertyRef = PropertyRef(
        "table_name", description="Name of the Azure Storage table."
    )


@dataclass(frozen=True)
class AzureStorageTableToStorageTableServiceRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:AzureStorageTableService)-[:CONTAINS]->(:AzureStorageTable)
class AzureStorageTableToStorageTableServiceRel(CartographyRelSchema):
    """An Azure Table Storage service contains the table."""

    target_node_label: str = "AzureStorageTableService"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("service_id")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "CONTAINS"
    properties: AzureStorageTableToStorageTableServiceRelProperties = (
        AzureStorageTableToStorageTableServiceRelProperties()
    )


@dataclass(frozen=True)
class AzureStorageTableToSubscriptionRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:AzureSubscription)-[:RESOURCE]->(:AzureStorageTable)
class AzureStorageTableToSubscriptionRel(CartographyRelSchema):
    """An Azure subscription contains the table as a resource."""

    target_node_label: str = "AzureSubscription"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("AZURE_SUBSCRIPTION_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: AzureStorageTableToSubscriptionRelProperties = (
        AzureStorageTableToSubscriptionRelProperties()
    )


@dataclass(frozen=True)
class AzureStorageTableSchema(CartographyNodeSchema):
    """An Azure Table Storage table hosted by a table service."""

    label: str = "AzureStorageTable"
    properties: AzureStorageTableProperties = AzureStorageTableProperties()
    sub_resource_relationship: AzureStorageTableToSubscriptionRel = (
        AzureStorageTableToSubscriptionRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            AzureStorageTableToStorageTableServiceRel(),
        ]
    )

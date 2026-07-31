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
class AzureCosmosDBLocationProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "id",
        description="Unique identifier of the regional account location.",
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    locationname: PropertyRef = PropertyRef(
        "location_name",
        description="Azure region name.",
    )
    documentendpoint: PropertyRef = PropertyRef(
        "document_endpoint",
        description="Connection endpoint for the account in this region.",
    )
    provisioningstate: PropertyRef = PropertyRef(
        "provisioning_state",
        description="Provisioning state of the resource.",
    )
    failoverpriority: PropertyRef = PropertyRef(
        "failover_priority",
        description="Failover priority of the region, where zero is the write region.",
    )
    iszoneredundant: PropertyRef = PropertyRef(
        "is_zone_redundant",
        description="Whether the regional deployment uses availability zones.",
    )


@dataclass(frozen=True)
class AzureCosmosDBLocationWriteToAzureCosmosDBAccountRelProperties(
    CartographyRelProperties
):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:AzureCosmosDBAccount)-[:CAN_WRITE_FROM]->(:AzureCosmosDBLocation)
class AzureCosmosDBLocationWriteToAzureCosmosDBAccountRel(CartographyRelSchema):
    """A Cosmos DB account can accept writes in the location."""

    target_node_label: str = "AzureCosmosDBAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("db_write_account_id")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "CAN_WRITE_FROM"
    properties: AzureCosmosDBLocationWriteToAzureCosmosDBAccountRelProperties = (
        AzureCosmosDBLocationWriteToAzureCosmosDBAccountRelProperties()
    )


@dataclass(frozen=True)
class AzureCosmosDBLocationReadToAzureCosmosDBAccountRelProperties(
    CartographyRelProperties
):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:AzureCosmosDBAccount)-[:CAN_READ_FROM]->(:AzureCosmosDBLocation)
class AzureCosmosDBLocationReadToAzureCosmosDBAccountRel(CartographyRelSchema):
    """A Cosmos DB account can serve reads from the location."""

    target_node_label: str = "AzureCosmosDBAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("db_read_account_id")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "CAN_READ_FROM"
    properties: AzureCosmosDBLocationReadToAzureCosmosDBAccountRelProperties = (
        AzureCosmosDBLocationReadToAzureCosmosDBAccountRelProperties()
    )


@dataclass(frozen=True)
class AzureCosmosDBLocationAssociatedToAzureCosmosDBAccountRelProperties(
    CartographyRelProperties
):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:AzureCosmosDBAccount)-[:ASSOCIATED_WITH]->(:AzureCosmosDBLocation)
class AzureCosmosDBLocationAssociatedToAzureCosmosDBAccountRel(CartographyRelSchema):
    """A Cosmos DB account is deployed in the associated location."""

    target_node_label: str = "AzureCosmosDBAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("db_associated_account_id")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "ASSOCIATED_WITH"
    properties: AzureCosmosDBLocationAssociatedToAzureCosmosDBAccountRelProperties = (
        AzureCosmosDBLocationAssociatedToAzureCosmosDBAccountRelProperties()
    )


@dataclass(frozen=True)
class AzureCosmosDBLocationToSubscriptionRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:AzureSubscription)-[:RESOURCE]->(:AzureCosmosDBLocation)
class AzureCosmosDBLocationToSubscriptionRel(CartographyRelSchema):
    """An Azure subscription contains the Cosmos DB location as a resource."""

    target_node_label: str = "AzureSubscription"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("AZURE_SUBSCRIPTION_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: AzureCosmosDBLocationToSubscriptionRelProperties = (
        AzureCosmosDBLocationToSubscriptionRelProperties()
    )


@dataclass(frozen=True)
class AzureCosmosDBLocationSchema(CartographyNodeSchema):
    """An Azure region associated with a Cosmos DB account deployment."""

    label: str = "AzureCosmosDBLocation"
    properties: AzureCosmosDBLocationProperties = AzureCosmosDBLocationProperties()
    sub_resource_relationship: AzureCosmosDBLocationToSubscriptionRel = (
        AzureCosmosDBLocationToSubscriptionRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            AzureCosmosDBLocationWriteToAzureCosmosDBAccountRel(),
            AzureCosmosDBLocationReadToAzureCosmosDBAccountRel(),
            AzureCosmosDBLocationAssociatedToAzureCosmosDBAccountRel(),
        ]
    )

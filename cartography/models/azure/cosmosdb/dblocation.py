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
    id: PropertyRef = PropertyRef("id")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    locationname: PropertyRef = PropertyRef("location_name")
    documentendpoint: PropertyRef = PropertyRef("document_endpoint")
    provisioningstate: PropertyRef = PropertyRef("provisioning_state")
    failoverpriority: PropertyRef = PropertyRef("failover_priority")
    iszoneredundant: PropertyRef = PropertyRef("is_zone_redundant")


@dataclass(frozen=True)
class AzureCosmosDBLocationWriteToAzureCosmosDBAccountProperties(
    CartographyRelProperties
):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:AzureCosmosDBAccount)-[:CAN_WRITE_FROM]->(:AzureCosmosDBLocation)
class AzureCosmosDBLocationWriteToAzureCosmosDBAccountRel(CartographyRelSchema):
    target_node_label: str = "AzureCosmosDBAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("db_write_account_id")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "CAN_WRITE_FROM"
    properties: AzureCosmosDBLocationWriteToAzureCosmosDBAccountProperties = (
        AzureCosmosDBLocationWriteToAzureCosmosDBAccountProperties()
    )


@dataclass(frozen=True)
class AzureCosmosDBLocationReadToAzureCosmosDBAccountProperties(
    CartographyRelProperties
):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:AzureCosmosDBAccount)-[:CAN_READ_FROM]->(:AzureCosmosDBLocation)
class AzureCosmosDBLocationReadToAzureCosmosDBAccountRel(CartographyRelSchema):
    target_node_label: str = "AzureCosmosDBAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("db_read_account_id")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "CAN_READ_FROM"
    properties: AzureCosmosDBLocationReadToAzureCosmosDBAccountProperties = (
        AzureCosmosDBLocationReadToAzureCosmosDBAccountProperties()
    )


@dataclass(frozen=True)
class AzureCosmosDBLocationAssociatedToAzureCosmosDBAccountProperties(
    CartographyRelProperties
):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:AzureCosmosDBAccount)-[:ASSOCIATED_WITH]->(:AzureCosmosDBLocation)
class AzureCosmosDBLocationAssociatedToAzureCosmosDBAccountRel(CartographyRelSchema):
    target_node_label: str = "AzureCosmosDBAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("db_associated_account_id")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "ASSOCIATED_WITH"
    properties: AzureCosmosDBLocationAssociatedToAzureCosmosDBAccountProperties = (
        AzureCosmosDBLocationAssociatedToAzureCosmosDBAccountProperties()
    )


@dataclass(frozen=True)
class AzureCosmosDBLocationToSubscriptionRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:AzureSubscription)-[:RESOURCE]->(:AzureCosmosDBLocation)
class AzureCosmosDBLocationToSubscriptionRel(CartographyRelSchema):
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

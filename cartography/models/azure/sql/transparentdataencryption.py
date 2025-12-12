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
class AzureTransparentDataEncryptionProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    name: PropertyRef = PropertyRef("name")
    location: PropertyRef = PropertyRef("location")
    status: PropertyRef = PropertyRef("status")


@dataclass(frozen=True)
class AzureTransparentDataEncryptionToSQLDatabaseProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:AzureSQLDatabase)-[:CONTAINS]->(:AzureTransparentDataEncryption)
class AzureTransparentDataEncryptionToSQLDatabaseRel(CartographyRelSchema):
    target_node_label: str = "AzureSQLDatabase"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("database_id")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "CONTAINS"
    properties: AzureTransparentDataEncryptionToSQLDatabaseProperties = (
        AzureTransparentDataEncryptionToSQLDatabaseProperties()
    )


@dataclass(frozen=True)
class AzureTransparentDataEncryptionToSubscriptionRelProperties(
    CartographyRelProperties
):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:AzureSubscription)-[:RESOURCE]->(:AzureTransparentDataEncryption)
class AzureTransparentDataEncryptionToSubscriptionRel(CartographyRelSchema):
    target_node_label: str = "AzureSubscription"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("AZURE_SUBSCRIPTION_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: AzureTransparentDataEncryptionToSubscriptionRelProperties = (
        AzureTransparentDataEncryptionToSubscriptionRelProperties()
    )


@dataclass(frozen=True)
class AzureTransparentDataEncryptionSchema(CartographyNodeSchema):
    label: str = "AzureTransparentDataEncryption"
    properties: AzureTransparentDataEncryptionProperties = (
        AzureTransparentDataEncryptionProperties()
    )
    sub_resource_relationship: AzureTransparentDataEncryptionToSubscriptionRel = (
        AzureTransparentDataEncryptionToSubscriptionRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            AzureTransparentDataEncryptionToSQLDatabaseRel(),
        ]
    )

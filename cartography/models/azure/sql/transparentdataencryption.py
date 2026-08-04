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
    id: PropertyRef = PropertyRef(
        "id",
        description="Azure resource ID for the transparent data encryption configuration.",
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    name: PropertyRef = PropertyRef("name", description="Azure resource name.")
    location: PropertyRef = PropertyRef(
        "location", description="Azure region of the resource."
    )
    status: PropertyRef = PropertyRef(
        "status", description="State of transparent data encryption."
    )


@dataclass(frozen=True)
class AzureTransparentDataEncryptionToSQLDatabaseRelProperties(
    CartographyRelProperties
):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:AzureSQLDatabase)-[:CONTAINS]->(:AzureTransparentDataEncryption)
class AzureTransparentDataEncryptionToSQLDatabaseRel(CartographyRelSchema):
    """An Azure SQL database contains this encryption configuration."""

    target_node_label: str = "AzureSQLDatabase"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("database_id")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "CONTAINS"
    properties: AzureTransparentDataEncryptionToSQLDatabaseRelProperties = (
        AzureTransparentDataEncryptionToSQLDatabaseRelProperties()
    )


@dataclass(frozen=True)
class AzureTransparentDataEncryptionToSubscriptionRelProperties(
    CartographyRelProperties
):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:AzureSubscription)-[:RESOURCE]->(:AzureTransparentDataEncryption)
class AzureTransparentDataEncryptionToSubscriptionRel(CartographyRelSchema):
    """An Azure subscription contains this encryption configuration resource."""

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
    """The transparent data encryption configuration for an Azure SQL database."""

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

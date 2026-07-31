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
class AzureKeyVaultProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "id", description="Full Azure resource ID of the vault."
    )
    name: PropertyRef = PropertyRef("name", description="Name of the vault.")
    location: PropertyRef = PropertyRef(
        "location", description="Azure region where the vault is deployed."
    )
    tenant_id: PropertyRef = PropertyRef(
        "tenant_id", description="Microsoft tenant ID associated with the vault."
    )
    sku_name: PropertyRef = PropertyRef(
        "sku_name", description="Name of the vault pricing SKU."
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


# --- Relationship Definitions ---
@dataclass(frozen=True)
class AzureKeyVaultToSubscriptionRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AzureKeyVaultToSubscriptionRel(CartographyRelSchema):
    """An Azure subscription contains the key vault as a resource."""

    target_node_label: str = "AzureSubscription"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("AZURE_SUBSCRIPTION_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: AzureKeyVaultToSubscriptionRelProperties = (
        AzureKeyVaultToSubscriptionRelProperties()
    )


# --- Main Schema ---
@dataclass(frozen=True)
class AzureKeyVaultSchema(CartographyNodeSchema):
    """An Azure Key Vault for keys, secrets, and certificates."""

    label: str = "AzureKeyVault"
    properties: AzureKeyVaultProperties = AzureKeyVaultProperties()
    sub_resource_relationship: AzureKeyVaultToSubscriptionRel = (
        AzureKeyVaultToSubscriptionRel()
    )

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
class AzureKeyVaultKeyProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id")
    name: PropertyRef = PropertyRef("name")
    enabled: PropertyRef = PropertyRef("enabled")
    created_on: PropertyRef = PropertyRef("created_on")
    updated_on: PropertyRef = PropertyRef("updated_on")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


# --- Relationship Definitions ---
@dataclass(frozen=True)
class AzureKeyVaultKeyToVaultRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AzureKeyVaultKeyToVaultRel(CartographyRelSchema):
    target_node_label: str = "AzureKeyVault"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("VAULT_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "CONTAINS"
    properties: AzureKeyVaultKeyToVaultRelProperties = (
        AzureKeyVaultKeyToVaultRelProperties()
    )


@dataclass(frozen=True)
class AzureKeyVaultKeyToSubscriptionRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AzureKeyVaultKeyToSubscriptionRel(CartographyRelSchema):
    target_node_label: str = "AzureSubscription"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("AZURE_SUBSCRIPTION_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: AzureKeyVaultKeyToSubscriptionRelProperties = (
        AzureKeyVaultKeyToSubscriptionRelProperties()
    )


# --- Main Schema ---
@dataclass(frozen=True)
class AzureKeyVaultKeySchema(CartographyNodeSchema):
    label: str = "AzureKeyVaultKey"
    properties: AzureKeyVaultKeyProperties = AzureKeyVaultKeyProperties()
    other_relationships: OtherRelationships = OtherRelationships(
        rels=[
            AzureKeyVaultKeyToVaultRel(),
        ],
    )
    sub_resource_relationship: AzureKeyVaultKeyToSubscriptionRel = (
        AzureKeyVaultKeyToSubscriptionRel()
    )

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
from cartography.models.ontology.labels import SECRET

logger = logging.getLogger(__name__)


# --- Node Definitions ---
@dataclass(frozen=True)
class AzureKeyVaultSecretProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "id", description="Azure Key Vault secret identifier."
    )
    name: PropertyRef = PropertyRef("name", description="Name of the secret.")
    enabled: PropertyRef = PropertyRef(
        "enabled", description="Whether the secret is enabled."
    )
    created_on: PropertyRef = PropertyRef(
        "created_on", description="Timestamp when the secret was created."
    )
    updated_on: PropertyRef = PropertyRef(
        "updated_on", description="Timestamp when the secret was last updated."
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


# --- Relationship Definitions ---
@dataclass(frozen=True)
class AzureKeyVaultSecretToVaultRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AzureKeyVaultSecretToVaultRel(CartographyRelSchema):
    """An Azure key vault contains the secret."""

    target_node_label: str = "AzureKeyVault"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("VAULT_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "CONTAINS"
    properties: AzureKeyVaultSecretToVaultRelProperties = (
        AzureKeyVaultSecretToVaultRelProperties()
    )


@dataclass(frozen=True)
class AzureKeyVaultSecretToSubscriptionRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AzureKeyVaultSecretToSubscriptionRel(CartographyRelSchema):
    """An Azure subscription contains the secret as a resource."""

    target_node_label: str = "AzureSubscription"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("AZURE_SUBSCRIPTION_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: AzureKeyVaultSecretToSubscriptionRelProperties = (
        AzureKeyVaultSecretToSubscriptionRelProperties()
    )


# --- Main Schema ---
@dataclass(frozen=True)
class AzureKeyVaultSecretSchema(CartographyNodeSchema):
    """A secret managed in Azure Key Vault."""

    label: str = "AzureKeyVaultSecret"
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(
        [SECRET]
    )  # Secret label is used for ontology mapping
    properties: AzureKeyVaultSecretProperties = AzureKeyVaultSecretProperties()
    other_relationships: OtherRelationships = OtherRelationships(
        rels=[
            AzureKeyVaultSecretToVaultRel(),
        ],
    )
    sub_resource_relationship: AzureKeyVaultSecretToSubscriptionRel = (
        AzureKeyVaultSecretToSubscriptionRel()
    )

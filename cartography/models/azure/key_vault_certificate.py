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
from cartography.models.ontology.labels import CERTIFICATE

logger = logging.getLogger(__name__)


# --- Node Definitions ---
@dataclass(frozen=True)
class AzureKeyVaultCertificateProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "id", description="Azure Key Vault certificate identifier."
    )
    name: PropertyRef = PropertyRef("name", description="Name of the certificate.")
    enabled: PropertyRef = PropertyRef(
        "enabled", description="Whether the certificate is enabled."
    )
    created_on: PropertyRef = PropertyRef(
        "created_on", description="Timestamp when the certificate was created."
    )
    updated_on: PropertyRef = PropertyRef(
        "updated_on", description="Timestamp when the certificate was last updated."
    )
    x5t: PropertyRef = PropertyRef(
        "x5t", description="Hexadecimal X.509 certificate thumbprint."
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


# --- Relationship Definitions ---
@dataclass(frozen=True)
class AzureKeyVaultCertificateToVaultRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AzureKeyVaultCertificateToVaultRel(CartographyRelSchema):
    """An Azure key vault contains the certificate."""

    target_node_label: str = "AzureKeyVault"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("VAULT_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "CONTAINS"
    properties: AzureKeyVaultCertificateToVaultRelProperties = (
        AzureKeyVaultCertificateToVaultRelProperties()
    )


@dataclass(frozen=True)
class AzureKeyVaultCertificateToSubscriptionRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AzureKeyVaultCertificateToSubscriptionRel(CartographyRelSchema):
    """An Azure subscription contains the certificate as a resource."""

    target_node_label: str = "AzureSubscription"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("AZURE_SUBSCRIPTION_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: AzureKeyVaultCertificateToSubscriptionRelProperties = (
        AzureKeyVaultCertificateToSubscriptionRelProperties()
    )


# --- Main Schema ---
@dataclass(frozen=True)
class AzureKeyVaultCertificateSchema(CartographyNodeSchema):
    """A certificate managed in Azure Key Vault."""

    label: str = "AzureKeyVaultCertificate"
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels([CERTIFICATE])
    properties: AzureKeyVaultCertificateProperties = (
        AzureKeyVaultCertificateProperties()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        rels=[
            AzureKeyVaultCertificateToVaultRel(),
        ],
    )
    sub_resource_relationship: AzureKeyVaultCertificateToSubscriptionRel = (
        AzureKeyVaultCertificateToSubscriptionRel()
    )

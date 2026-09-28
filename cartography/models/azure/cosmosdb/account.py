from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.relationships import CartographyRelProperties
from cartography.models.core.relationships import CartographyRelSchema
from cartography.models.core.relationships import LinkDirection
from cartography.models.core.relationships import make_target_node_matcher
from cartography.models.core.relationships import TargetNodeMatcher


@dataclass(frozen=True)
class AzureCosmosDBAccountProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id", description="Azure resource ID.")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    type: PropertyRef = PropertyRef("type", description="Azure resource type.")
    resourcegroup: PropertyRef = PropertyRef(
        "resourceGroup",
        description="Name of the Azure resource group.",
    )
    location: PropertyRef = PropertyRef(
        "location",
        description="Azure region where the resource is located.",
    )
    kind: PropertyRef = PropertyRef(
        "kind",
        description="API kind supported by the account.",
    )
    name: PropertyRef = PropertyRef("name", description="Name of the Azure resource.")
    ipranges: PropertyRef = PropertyRef(
        "ipruleslist",
        description="IP addresses or CIDR ranges allowed by the account firewall.",
    )
    capabilities: PropertyRef = PropertyRef(
        "capabilities",
        description="Capabilities enabled for the account.",
    )
    documentendpoint: PropertyRef = PropertyRef(
        "document_endpoint",
        description="Connection endpoint for the account.",
    )
    virtualnetworkfilterenabled: PropertyRef = PropertyRef(
        "is_virtual_network_filter_enabled",
        description="Whether virtual network access control rules are enabled.",
    )
    enableautomaticfailover: PropertyRef = PropertyRef(
        "enable_automatic_failover",
        description="Whether Azure automatically promotes a write region after an outage.",
    )
    provisioningstate: PropertyRef = PropertyRef(
        "provisioning_state",
        description="Provisioning state of the resource.",
    )
    multiplewritelocations: PropertyRef = PropertyRef(
        "enable_multiple_write_locations",
        description="Whether writes are enabled in multiple Azure regions.",
    )
    accountoffertype: PropertyRef = PropertyRef(
        "database_account_offer_type",
        description="Offer type of the database account.",
    )
    publicnetworkaccess: PropertyRef = PropertyRef(
        "public_network_access",
        description="Whether public network access is enabled for the account.",
    )
    enablecassandraconnector: PropertyRef = PropertyRef(
        "enable_cassandra_connector",
        description="Whether the Cassandra connector is enabled.",
    )
    connectoroffer: PropertyRef = PropertyRef(
        "connector_offer",
        description="Offer type of the Cassandra connector.",
    )
    disablekeybasedmetadatawriteaccess: PropertyRef = PropertyRef(
        "disable_key_based_metadata_write_access",
        description="Whether account keys are blocked from writing resource metadata.",
    )
    keyvaulturi: PropertyRef = PropertyRef(
        "key_vault_key_uri",
        description="Key Vault URI of the customer-managed encryption key.",
    )
    enablefreetier: PropertyRef = PropertyRef(
        "enable_free_tier",
        description="Whether the account uses the Azure Cosmos DB free tier.",
    )
    enableanalyticalstorage: PropertyRef = PropertyRef(
        "enable_analytical_storage",
        description="Whether analytical storage is enabled.",
    )
    defaultconsistencylevel: PropertyRef = PropertyRef(
        "consistency_policy.default_consistency_level",
        description="Default consistency level for the account.",
    )
    maxstalenessprefix: PropertyRef = PropertyRef(
        "consistency_policy.max_staleness_prefix",
        description="Maximum stale request count allowed for bounded staleness.",
    )
    maxintervalinseconds: PropertyRef = PropertyRef(
        "consistency_policy.max_interval_in_seconds",
        description="Maximum staleness interval in seconds for bounded staleness.",
    )


@dataclass(frozen=True)
class AzureCosmosDBAccountToSubscriptionRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:AzureSubscription)-[:RESOURCE]->(:AzureCosmosDBAccount)
class AzureCosmosDBAccountToSubscriptionRel(CartographyRelSchema):
    """An Azure subscription contains the Cosmos DB account as a resource."""

    target_node_label: str = "AzureSubscription"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("AZURE_SUBSCRIPTION_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: AzureCosmosDBAccountToSubscriptionRelProperties = (
        AzureCosmosDBAccountToSubscriptionRelProperties()
    )


@dataclass(frozen=True)
class AzureCosmosDBAccountSchema(CartographyNodeSchema):
    """An Azure Cosmos DB account that hosts databases and related settings."""

    label: str = "AzureCosmosDBAccount"
    properties: AzureCosmosDBAccountProperties = AzureCosmosDBAccountProperties()
    sub_resource_relationship: AzureCosmosDBAccountToSubscriptionRel = (
        AzureCosmosDBAccountToSubscriptionRel()
    )

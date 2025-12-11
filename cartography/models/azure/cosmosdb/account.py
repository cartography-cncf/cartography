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
    id: PropertyRef = PropertyRef("id")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    type: PropertyRef = PropertyRef("type")
    resourcegroup: PropertyRef = PropertyRef("resourceGroup")
    location: PropertyRef = PropertyRef("location")
    kind: PropertyRef = PropertyRef("kind")
    name: PropertyRef = PropertyRef("name")
    ipranges: PropertyRef = PropertyRef("ipruleslist")
    capabilities: PropertyRef = PropertyRef("capabilities")
    documentendpoint: PropertyRef = PropertyRef("document_endpoint")
    virtualnetworkfilterenabled: PropertyRef = PropertyRef(
        "is_virtual_network_filter_enabled"
    )
    enableautomaticfailover: PropertyRef = PropertyRef("enable_automatic_failover")
    provisioningstate: PropertyRef = PropertyRef("provisioning_state")
    multiplewritelocations: PropertyRef = PropertyRef("enable_multiple_write_locations")
    accountoffertype: PropertyRef = PropertyRef("database_account_offer_type")
    publicnetworkaccess: PropertyRef = PropertyRef("public_network_access")
    enablecassandraconnector: PropertyRef = PropertyRef("enable_cassandra_connector")
    connectoroffer: PropertyRef = PropertyRef("connector_offer")
    disablekeybasedmetadatawriteaccess: PropertyRef = PropertyRef(
        "disable_key_based_metadata_write_access"
    )
    keyvaulturi: PropertyRef = PropertyRef("key_vault_key_uri")
    enablefreetier: PropertyRef = PropertyRef("enable_free_tier")
    enableanalyticalstorage: PropertyRef = PropertyRef("enable_analytical_storage")
    defaultconsistencylevel: PropertyRef = PropertyRef(
        "consistency_policy.default_consistency_level"
    )
    maxstalenessprefix: PropertyRef = PropertyRef(
        "consistency_policy.max_staleness_prefix"
    )
    maxintervalinseconds: PropertyRef = PropertyRef(
        "consistency_policy.max_interval_in_seconds"
    )


@dataclass(frozen=True)
class AzureCosmosDBAccountToSubscriptionRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:AzureSubscription)-[:RESOURCE]->(:AzureCosmosDBAccount)
class AzureCosmosDBAccountToSubscriptionRel(CartographyRelSchema):
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
    label: str = "AzureCosmosDBAccount"
    properties: AzureCosmosDBAccountProperties = AzureCosmosDBAccountProperties()
    sub_resource_relationship: AzureCosmosDBAccountToSubscriptionRel = (
        AzureCosmosDBAccountToSubscriptionRel()
    )

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
class AzureSQLServerProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "id", description="Azure resource ID for the SQL logical server."
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    name: PropertyRef = PropertyRef("name", description="Azure resource name.")
    resourcegroup: PropertyRef = PropertyRef(
        "resourceGroup", description="Name of the containing Azure resource group."
    )
    location: PropertyRef = PropertyRef(
        "location", description="Azure region of the resource."
    )
    kind: PropertyRef = PropertyRef(
        "kind", description="Resource kind reported by Azure."
    )
    state: PropertyRef = PropertyRef(
        "state", description="Current state of the SQL logical server."
    )
    version: PropertyRef = PropertyRef(
        "version", description="SQL logical server version."
    )
    public_network_access: PropertyRef = PropertyRef(
        "public_network_access",
        description="Whether public network access is enabled for the server.",
    )
    minimal_tls_version: PropertyRef = PropertyRef(
        "minimal_tls_version",
        description="Minimum TLS version accepted by the server.",
    )


@dataclass(frozen=True)
class AzureSQLServerToSubscriptionRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:AzureSubscription)-[:RESOURCE]->(:AzureSQLServer)
class AzureSQLServerToSubscriptionRel(CartographyRelSchema):
    """An Azure subscription contains this SQL logical server resource."""

    target_node_label: str = "AzureSubscription"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("AZURE_SUBSCRIPTION_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: AzureSQLServerToSubscriptionRelProperties = (
        AzureSQLServerToSubscriptionRelProperties()
    )


@dataclass(frozen=True)
class AzureSQLServerSchema(CartographyNodeSchema):
    """An Azure SQL logical server that hosts databases and related resources."""

    label: str = "AzureSQLServer"
    properties: AzureSQLServerProperties = AzureSQLServerProperties()
    sub_resource_relationship: AzureSQLServerToSubscriptionRel = (
        AzureSQLServerToSubscriptionRel()
    )

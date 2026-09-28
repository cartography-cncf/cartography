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
class AzureServerADAdministratorProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "id", description="Azure resource ID for the SQL server administrator."
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    name: PropertyRef = PropertyRef("name", description="Azure resource name.")
    login: PropertyRef = PropertyRef(
        "login", description="Login name of the server administrator."
    )
    administratortype: PropertyRef = PropertyRef(
        "administrator_type", description="Type of server administrator."
    )


@dataclass(frozen=True)
class AzureServerADAdministratorToSQLServerRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:AzureSQLServer)-[:ADMINISTERED_BY]->(:AzureServerADAdministrator)
class AzureServerADAdministratorToSQLServerRel(CartographyRelSchema):
    """An Azure SQL logical server is administered by this identity."""

    target_node_label: str = "AzureSQLServer"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("server_id")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "ADMINISTERED_BY"
    properties: AzureServerADAdministratorToSQLServerRelProperties = (
        AzureServerADAdministratorToSQLServerRelProperties()
    )


@dataclass(frozen=True)
class AzureServerADAdministratorToSubscriptionRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:AzureSubscription)-[:RESOURCE]->(:AzureServerADAdministrator)
class AzureServerADAdministratorToSubscriptionRel(CartographyRelSchema):
    """An Azure subscription contains this SQL server administrator resource."""

    target_node_label: str = "AzureSubscription"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("AZURE_SUBSCRIPTION_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: AzureServerADAdministratorToSubscriptionRelProperties = (
        AzureServerADAdministratorToSubscriptionRelProperties()
    )


@dataclass(frozen=True)
class AzureServerADAdministratorSchema(CartographyNodeSchema):
    """A Microsoft Entra administrator configured for an Azure SQL server."""

    label: str = "AzureServerADAdministrator"
    properties: AzureServerADAdministratorProperties = (
        AzureServerADAdministratorProperties()
    )
    sub_resource_relationship: AzureServerADAdministratorToSubscriptionRel = (
        AzureServerADAdministratorToSubscriptionRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            AzureServerADAdministratorToSQLServerRel(),
        ]
    )

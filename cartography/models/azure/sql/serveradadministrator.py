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
    id: PropertyRef = PropertyRef("id")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    name: PropertyRef = PropertyRef("name")
    login: PropertyRef = PropertyRef("login")
    administratortype: PropertyRef = PropertyRef("administrator_type")


@dataclass(frozen=True)
class AzureServerADAdministratorToSQLServerProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:AzureSQLServer)-[:ADMINISTERED_BY]->(:AzureServerADAdministrator)
class AzureServerADAdministratorToSQLServerRel(CartographyRelSchema):
    target_node_label: str = "AzureSQLServer"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("server_id")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "ADMINISTERED_BY"
    properties: AzureServerADAdministratorToSQLServerProperties = (
        AzureServerADAdministratorToSQLServerProperties()
    )


@dataclass(frozen=True)
class AzureServerADAdministratorToSubscriptionRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:AzureSubscription)-[:RESOURCE]->(:AzureServerADAdministrator)
class AzureServerADAdministratorToSubscriptionRel(CartographyRelSchema):
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

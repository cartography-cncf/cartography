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
from cartography.models.extra_labels import IP_PERMISSION_INBOUND
from cartography.models.extra_labels import IP_RULE


@dataclass(frozen=True)
class AzureSQLServerFirewallRuleProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "id", description="Azure resource ID for the SQL server firewall rule."
    )
    name: PropertyRef = PropertyRef("name", description="Azure resource name.")
    start_ip_address: PropertyRef = PropertyRef(
        "start_ip_address",
        description="First IPv4 address in the allowed range.",
    )
    end_ip_address: PropertyRef = PropertyRef(
        "end_ip_address",
        description="Last IPv4 address in the allowed range.",
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AzureSQLServerFirewallRuleToSubscriptionRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:AzureSubscription)-[:RESOURCE]->(:AzureSQLServerFirewallRule)
class AzureSQLServerFirewallRuleToSubscriptionRel(CartographyRelSchema):
    """An Azure subscription contains this SQL server firewall rule resource."""

    target_node_label: str = "AzureSubscription"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("AZURE_SUBSCRIPTION_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: AzureSQLServerFirewallRuleToSubscriptionRelProperties = (
        AzureSQLServerFirewallRuleToSubscriptionRelProperties()
    )


@dataclass(frozen=True)
class AzureSQLServerFirewallRuleToSQLServerRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:AzureSQLServerFirewallRule)-[:MEMBER_OF_AZURE_SQL_SERVER]->(:AzureSQLServer)
class AzureSQLServerFirewallRuleToSQLServerRel(CartographyRelSchema):
    """This firewall rule applies to an Azure SQL logical server."""

    target_node_label: str = "AzureSQLServer"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("server_id")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "MEMBER_OF_AZURE_SQL_SERVER"
    properties: AzureSQLServerFirewallRuleToSQLServerRelProperties = (
        AzureSQLServerFirewallRuleToSQLServerRelProperties()
    )


@dataclass(frozen=True)
class AzureSQLServerFirewallRuleSchema(CartographyNodeSchema):
    """An Azure SQL server firewall rule for an allowed IPv4 address range."""

    label: str = "AzureSQLServerFirewallRule"
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(
        [IP_PERMISSION_INBOUND, IP_RULE]
    )
    properties: AzureSQLServerFirewallRuleProperties = (
        AzureSQLServerFirewallRuleProperties()
    )
    sub_resource_relationship: AzureSQLServerFirewallRuleToSubscriptionRel = (
        AzureSQLServerFirewallRuleToSubscriptionRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            AzureSQLServerFirewallRuleToSQLServerRel(),
        ],
    )

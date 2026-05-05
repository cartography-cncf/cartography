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


@dataclass(frozen=True)
class AzureSQLServerFirewallRuleProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id")
    name: PropertyRef = PropertyRef("name")
    start_ip_address: PropertyRef = PropertyRef("start_ip_address")
    end_ip_address: PropertyRef = PropertyRef("end_ip_address")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AzureSQLServerFirewallRuleToSubscriptionRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:AzureSubscription)-[:RESOURCE]->(:AzureSQLServerFirewallRule)
class AzureSQLServerFirewallRuleToSubscriptionRel(CartographyRelSchema):
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
    """SQL Server firewall rules are inbound IP allowlists, so they carry the
    cross-cloud `IpRule` and `IpPermissionInbound` labels."""

    label: str = "AzureSQLServerFirewallRule"
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(
        ["IpPermissionInbound", "IpRule"]
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

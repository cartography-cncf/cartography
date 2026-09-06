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
from cartography.models.extra_labels import IP_PERMISSION_EGRESS
from cartography.models.extra_labels import IP_PERMISSION_INBOUND
from cartography.models.extra_labels import IP_RULE


@dataclass(frozen=True)
class DOFirewallRuleProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "id",
        description="Stable, deterministic identifier for the firewall rule.",
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    canonical_name: PropertyRef = PropertyRef(
        "canonical_name",
        description="Canonical name for the firewall rule, derived from its properties.",
    )
    firewall_id: PropertyRef = PropertyRef(
        "firewall_id",
        extra_index=True,
        description="UUID of the firewall containing this rule.",
    )
    direction: PropertyRef = PropertyRef(
        "direction",
        description="Traffic direction: inbound or outbound.",
    )
    protocol: PropertyRef = PropertyRef(
        "protocol",
        description="Network protocol matched by the rule.",
    )
    ports: PropertyRef = PropertyRef(
        "ports",
        description="Port or inclusive port range matched by the rule.",
    )
    fromport: PropertyRef = PropertyRef(
        "fromport",
        description="Lowest transport-layer port matched by the rule.",
    )
    toport: PropertyRef = PropertyRef(
        "toport",
        description="Highest transport-layer port matched by the rule.",
    )
    action: PropertyRef = PropertyRef(
        "action",
        description="Firewall action applied when the rule matches.",
    )
    source_addresses: PropertyRef = PropertyRef(
        "source_addresses",
        description="Provider-scoped IP-range selector IDs for an inbound rule.",
    )
    destination_addresses: PropertyRef = PropertyRef(
        "destination_addresses",
        description="Provider-scoped IP-range selector IDs for an outbound rule.",
    )
    source_tags: PropertyRef = PropertyRef(
        "source_tags",
        description="DigitalOcean tags selected by an inbound rule.",
    )
    destination_tags: PropertyRef = PropertyRef(
        "destination_tags",
        description="DigitalOcean tags selected by an outbound rule.",
    )
    source_droplet_ids: PropertyRef = PropertyRef(
        "source_droplet_ids",
        description="Droplet IDs selected by an inbound rule.",
    )
    destination_droplet_ids: PropertyRef = PropertyRef(
        "destination_droplet_ids",
        description="Droplet IDs selected by an outbound rule.",
    )
    source_load_balancer_uids: PropertyRef = PropertyRef(
        "source_load_balancer_uids",
        description="Load-balancer UUIDs selected by an inbound rule.",
    )
    destination_load_balancer_uids: PropertyRef = PropertyRef(
        "destination_load_balancer_uids",
        description="Load-balancer UUIDs selected by an outbound rule.",
    )
    source_kubernetes_ids: PropertyRef = PropertyRef(
        "source_kubernetes_ids",
        description="Kubernetes-cluster IDs selected by an inbound rule.",
    )
    destination_kubernetes_ids: PropertyRef = PropertyRef(
        "destination_kubernetes_ids",
        description="Kubernetes-cluster IDs selected by an outbound rule.",
    )


@dataclass(frozen=True)
class DOFirewallRuleToAccountRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class DOFirewallRuleToAccountRel(CartographyRelSchema):
    """A DigitalOcean account contains the firewall rule as a resource."""

    target_node_label: str = "DOAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("ACCOUNT_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: DOFirewallRuleToAccountRelProperties = (
        DOFirewallRuleToAccountRelProperties()
    )


@dataclass(frozen=True)
class DOFirewallRuleToFirewallRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class DOFirewallRuleToFirewallRel(CartographyRelSchema):
    """A firewall rule belongs to a DigitalOcean firewall."""

    target_node_label: str = "DOFirewall"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("firewall_id")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "MEMBER_OF_DO_FIREWALL"
    properties: DOFirewallRuleToFirewallRelProperties = (
        DOFirewallRuleToFirewallRelProperties()
    )


@dataclass(frozen=True)
class DOFirewallRuleSelectorRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class DOFirewallRuleToSourceIpRangeRel(CartographyRelSchema):
    """An inbound rule selects one or more IP ranges as traffic sources."""

    target_node_label: str = "DOIpRange"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("source_addresses", one_to_many=True)},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "HAS_SOURCE"
    properties: DOFirewallRuleSelectorRelProperties = (
        DOFirewallRuleSelectorRelProperties()
    )


@dataclass(frozen=True)
class DOFirewallRuleToDestinationIpRangeRel(CartographyRelSchema):
    """An outbound rule selects one or more IP ranges as traffic destinations."""

    target_node_label: str = "DOIpRange"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("destination_addresses", one_to_many=True)},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "HAS_DESTINATION"
    properties: DOFirewallRuleSelectorRelProperties = (
        DOFirewallRuleSelectorRelProperties()
    )


@dataclass(frozen=True)
class DOFirewallRuleToSourceDropletRel(CartographyRelSchema):
    """An inbound rule selects one or more Droplets as traffic sources."""

    target_node_label: str = "DODroplet"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("source_droplet_ids", one_to_many=True)},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "HAS_SOURCE"
    properties: DOFirewallRuleSelectorRelProperties = (
        DOFirewallRuleSelectorRelProperties()
    )


@dataclass(frozen=True)
class DOFirewallRuleToDestinationDropletRel(CartographyRelSchema):
    """An outbound rule selects one or more Droplets as traffic destinations."""

    target_node_label: str = "DODroplet"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("destination_droplet_ids", one_to_many=True)},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "HAS_DESTINATION"
    properties: DOFirewallRuleSelectorRelProperties = (
        DOFirewallRuleSelectorRelProperties()
    )


@dataclass(frozen=True)
class DOFirewallRuleSchema(CartographyNodeSchema):
    """A directional traffic rule configured on a DigitalOcean Cloud Firewall."""

    label: str = "DOFirewallRule"
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(
        [
            IP_RULE,
            IP_PERMISSION_INBOUND.when(direction="inbound"),
            IP_PERMISSION_EGRESS.when(direction="outbound"),
        ],
    )
    properties: DOFirewallRuleProperties = DOFirewallRuleProperties()
    sub_resource_relationship: DOFirewallRuleToAccountRel = DOFirewallRuleToAccountRel()
    other_relationships: OtherRelationships = OtherRelationships(
        [
            DOFirewallRuleToFirewallRel(),
            DOFirewallRuleToSourceIpRangeRel(),
            DOFirewallRuleToDestinationIpRangeRel(),
            DOFirewallRuleToSourceDropletRel(),
            DOFirewallRuleToDestinationDropletRel(),
        ],
    )

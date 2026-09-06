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
from cartography.models.ontology.labels import NETWORK_ACCESS_CONTROL


@dataclass(frozen=True)
class DOFirewallProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "id",
        description="DigitalOcean firewall UUID.",
    )
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
    )
    name: PropertyRef = PropertyRef(
        "name",
        description="Firewall name.",
    )
    status: PropertyRef = PropertyRef(
        "status",
        description="Firewall operation status.",
    )
    created_at: PropertyRef = PropertyRef(
        "created_at",
        description="ISO 8601 timestamp when the firewall was created.",
    )
    tags: PropertyRef = PropertyRef(
        "tags",
        description="Tags assigned to the firewall.",
    )
    pending_changes: PropertyRef = PropertyRef(
        "pending_changes",
        description="Pending firewall changes reported by DigitalOcean.",
    )
    droplet_ids: PropertyRef = PropertyRef(
        "droplet_ids",
        description="IDs of Droplets protected by this firewall.",
    )


@dataclass(frozen=True)
class DOFirewallToAccountRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
    )


@dataclass(frozen=True)
class DOFirewallToAccountRel(CartographyRelSchema):
    """A DigitalOcean account contains the firewall as a resource."""

    target_node_label: str = "DOAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("ACCOUNT_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: DOFirewallToAccountRelProperties = DOFirewallToAccountRelProperties()


@dataclass(frozen=True)
class DOFirewallToDropletRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
    )


@dataclass(frozen=True)
class DOFirewallToDropletRel(CartographyRelSchema):
    """A DigitalOcean firewall protects one or more Droplets."""

    target_node_label: str = "DODroplet"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("droplet_ids", one_to_many=True)},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "PROTECTS"
    properties: DOFirewallToDropletRelProperties = DOFirewallToDropletRelProperties()


@dataclass(frozen=True)
class DOFirewallSchema(CartographyNodeSchema):
    """A DigitalOcean Cloud Firewall that controls Droplet network access."""

    label: str = "DOFirewall"
    properties: DOFirewallProperties = DOFirewallProperties()
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(
        [NETWORK_ACCESS_CONTROL],
    )
    sub_resource_relationship: DOFirewallToAccountRel = DOFirewallToAccountRel()
    other_relationships: OtherRelationships = OtherRelationships(
        [DOFirewallToDropletRel()],
    )

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
class GCPFirewallNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "id", description="A partial resource URI representing this Firewall."
    )
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last time the node was updated.",
    )
    direction: PropertyRef = PropertyRef(
        "direction",
        description="Either 'INGRESS' for inbound or 'EGRESS' for outbound.",
    )
    disabled: PropertyRef = PropertyRef(
        "disabled", description="Whether this firewall object is disabled."
    )
    name: PropertyRef = PropertyRef(
        "name", extra_index=True, description="Name assigned to this resource."
    )
    priority: PropertyRef = PropertyRef(
        "priority",
        description="The priority of this firewall rule from 1 (apply this first)-65535 (apply this last).",
    )
    self_link: PropertyRef = PropertyRef(
        "selfLink", description="The full resource URI to this firewall."
    )
    has_target_service_accounts: PropertyRef = PropertyRef(
        "has_target_service_accounts",
        description="Set to True if this Firewall has target service accounts defined. This field is currently a placeholder for future functionality to add GCP IAM objects to Cartography. If True, this firewall rule will only apply to GCP instances that use the specified target service account.",
    )


@dataclass(frozen=True)
class GCPFirewallToVpcRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last sync that observed this data.",
    )


@dataclass(frozen=True)
class GCPFirewallToVpcRel(CartographyRelSchema):
    target_node_label: str = "GCPVpc"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {
            "id": PropertyRef("vpc_partial_uri"),
        }
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: GCPFirewallToVpcRelProperties = GCPFirewallToVpcRelProperties()


@dataclass(frozen=True)
class GCPFirewallToProjectRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last sync that observed this data.",
    )


@dataclass(frozen=True)
class GCPFirewallToProjectRel(CartographyRelSchema):
    target_node_label: str = "GCPProject"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {
            "id": PropertyRef("PROJECT_ID", set_in_kwargs=True),
        }
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: GCPFirewallToProjectRelProperties = GCPFirewallToProjectRelProperties()


@dataclass(frozen=True)
class GCPFirewallSchema(CartographyNodeSchema):
    """Representation of a GCP [Firewall](https://cloud.google.com/compute/docs/reference/rest/v1/firewalls/list)."""

    label: str = "GCPFirewall"
    properties: GCPFirewallNodeProperties = GCPFirewallNodeProperties()
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(["NetworkAccessControl"])
    sub_resource_relationship: GCPFirewallToProjectRel = GCPFirewallToProjectRel()
    other_relationships: OtherRelationships = OtherRelationships(
        [
            GCPFirewallToVpcRel(),
        ]
    )

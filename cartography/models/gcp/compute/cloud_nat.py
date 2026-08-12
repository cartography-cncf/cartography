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
class GCPCloudNatNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "id", description="Stable identifier for this Cloud NAT config."
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    name: PropertyRef = PropertyRef(
        "name", extra_index=True, description="The name of the Cloud NAT config."
    )
    project_id: PropertyRef = PropertyRef(
        "project_id", description="The project ID that this Cloud NAT belongs to."
    )
    region: PropertyRef = PropertyRef(
        "region", description="The region where this Cloud NAT is configured."
    )
    router_id: PropertyRef = PropertyRef(
        "router_id",
        description="The partial URI of the parent Cloud Router that owns this NAT config.",
    )
    log_enabled: PropertyRef = PropertyRef(
        "log_enabled", description="Whether Cloud NAT logging is enabled."
    )
    log_filter: PropertyRef = PropertyRef(
        "log_filter",
        description="Cloud NAT log filter setting, such as `ERRORS_ONLY`, `TRANSLATIONS_ONLY`, or `ALL`.",
    )
    nat_ip_allocate_option: PropertyRef = PropertyRef(
        "nat_ip_allocate_option",
        description="Cloud NAT IP allocation mode, such as `AUTO_ONLY` or `MANUAL_ONLY`.",
    )
    source_subnetwork_ip_ranges_to_nat: PropertyRef = PropertyRef(
        "source_subnetwork_ip_ranges_to_nat",
        description="Source subnetwork IP range selection configured for this Cloud NAT.",
    )


@dataclass(frozen=True)
class GCPCloudNatToProjectRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class GCPCloudNatToProjectRel(CartographyRelSchema):
    target_node_label: str = "GCPProject"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {
            "id": PropertyRef("PROJECT_ID", set_in_kwargs=True),
        },
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: GCPCloudNatToProjectRelProperties = GCPCloudNatToProjectRelProperties()


@dataclass(frozen=True)
class GCPCloudNatToRouterRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class GCPCloudNatToRouterRel(CartographyRelSchema):
    target_node_label: str = "GCPRouter"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {
            "id": PropertyRef("router_id"),
        },
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "HAS_NAT"
    properties: GCPCloudNatToRouterRelProperties = GCPCloudNatToRouterRelProperties()


@dataclass(frozen=True)
class GCPCloudNatSchema(CartographyNodeSchema):
    """Representation of a GCP [Cloud NAT](https://cloud.google.com/nat/docs/reference/compute/rest/v1/routers)."""

    label: str = "GCPCloudNat"
    properties: GCPCloudNatNodeProperties = GCPCloudNatNodeProperties()
    sub_resource_relationship: GCPCloudNatToProjectRel = GCPCloudNatToProjectRel()
    other_relationships: OtherRelationships = OtherRelationships(
        [
            GCPCloudNatToRouterRel(),
        ],
    )

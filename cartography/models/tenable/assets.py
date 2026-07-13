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
class TenableAssetNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    # Core flags
    has_agent: PropertyRef = PropertyRef("has_agent")
    has_plugin_results: PropertyRef = PropertyRef("has_plugin_results")
    is_licensed: PropertyRef = PropertyRef("is_licensed")
    is_public: PropertyRef = PropertyRef("is_public")
    # Classification
    types: PropertyRef = PropertyRef("types")
    system_types: PropertyRef = PropertyRef("system_types")
    operating_systems: PropertyRef = PropertyRef("operating_systems")
    serial_number: PropertyRef = PropertyRef("serial_number", extra_index=True)
    tenable_agent_days_since_active: PropertyRef = PropertyRef(
        "tenable_agent_days_since_active"
    )
    # Timestamps (from asset.timestamps)
    created_at_timestamps: PropertyRef = PropertyRef("created_at_timestamps")
    updated_at_timestamps: PropertyRef = PropertyRef("updated_at_timestamps")
    first_seen_timestamps: PropertyRef = PropertyRef("first_seen_timestamps")
    last_seen_timestamps: PropertyRef = PropertyRef("last_seen_timestamps")
    # Scan info (from asset.scan)
    first_scan_time: PropertyRef = PropertyRef("first_scan_time")
    last_scan_time: PropertyRef = PropertyRef("last_scan_time")
    last_authenticated_scan_date: PropertyRef = PropertyRef(
        "last_authenticated_scan_date"
    )
    last_licensed_scan_date: PropertyRef = PropertyRef("last_licensed_scan_date")
    last_scan_id: PropertyRef = PropertyRef("last_scan_id")
    # Network (from asset.network) — detail in TenableNetwork
    network_id: PropertyRef = PropertyRef("network_id")
    fqdn: PropertyRef = PropertyRef("fqdn", extra_index=True)
    ipv4s: PropertyRef = PropertyRef("ipv4s")
    ipv6s: PropertyRef = PropertyRef("ipv6s")
    fqdns: PropertyRef = PropertyRef("fqdns")
    hostnames: PropertyRef = PropertyRef("hostnames")
    mac_addresses: PropertyRef = PropertyRef("mac_addresses")
    # Cloud identifiers — detail in TenableAssetAWS / TenableAssetAzure / TenableAssetGCP
    aws_ec2_instance_id: PropertyRef = PropertyRef(
        "aws_ec2_instance_id", extra_index=True
    )
    azure_vm_id: PropertyRef = PropertyRef("azure_vm_id", extra_index=True)
    gcp_instance_id: PropertyRef = PropertyRef("gcp_instance_id", extra_index=True)
    # Ratings (from asset.ratings)
    acr_score: PropertyRef = PropertyRef("acr_score")
    aes_score: PropertyRef = PropertyRef("aes_score")


@dataclass(frozen=True)
class TenableAssetToTenantRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


# (:TenableTenant)-[:RESOURCE]->(:TenableAsset)
@dataclass(frozen=True)
class TenableAssetToTenantRel(CartographyRelSchema):
    target_node_label: str = "TenableTenant"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("TENABLE_TENANT_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: TenableAssetToTenantRelProperties = TenableAssetToTenantRelProperties()


@dataclass(frozen=True)
class TenableAssetToNetworkRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


# (:TenableAsset)-[:MEMBER_OF_NETWORK]->(:TenableNetwork)
@dataclass(frozen=True)
class TenableAssetToNetworkRel(CartographyRelSchema):
    target_node_label: str = "TenableNetwork"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("network_id")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "MEMBER_OF_NETWORK"
    properties: TenableAssetToNetworkRelProperties = (
        TenableAssetToNetworkRelProperties()
    )


@dataclass(frozen=True)
class TenableAssetToAWSRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


# (:TenableAsset)-[:HAS_AWS_INFO]->(:TenableAssetAWS)
@dataclass(frozen=True)
class TenableAssetToAWSRel(CartographyRelSchema):
    target_node_label: str = "TenableAssetAWS"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("aws_ec2_instance_id")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "HAS_AWS_INFO"
    properties: TenableAssetToAWSRelProperties = TenableAssetToAWSRelProperties()


@dataclass(frozen=True)
class TenableAssetToAzureRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


# (:TenableAsset)-[:HAS_AZURE_INFO]->(:TenableAssetAzure)
@dataclass(frozen=True)
class TenableAssetToAzureRel(CartographyRelSchema):
    target_node_label: str = "TenableAssetAzure"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("azure_vm_id")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "HAS_AZURE_INFO"
    properties: TenableAssetToAzureRelProperties = TenableAssetToAzureRelProperties()


@dataclass(frozen=True)
class TenableAssetToGCPRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


# (:TenableAsset)-[:HAS_GCP_INFO]->(:TenableAssetGCP)
@dataclass(frozen=True)
class TenableAssetToGCPRel(CartographyRelSchema):
    target_node_label: str = "TenableAssetGCP"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("gcp_instance_id")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "HAS_GCP_INFO"
    properties: TenableAssetToGCPRelProperties = TenableAssetToGCPRelProperties()


@dataclass(frozen=True)
class TenableAssetSchema(CartographyNodeSchema):
    label: str = "TenableAsset"
    properties: TenableAssetNodeProperties = TenableAssetNodeProperties()
    sub_resource_relationship: TenableAssetToTenantRel = TenableAssetToTenantRel()
    other_relationships: OtherRelationships = OtherRelationships(
        [
            TenableAssetToNetworkRel(),
            TenableAssetToAWSRel(),
            TenableAssetToAzureRel(),
            TenableAssetToGCPRel(),
        ]
    )

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
    id: PropertyRef = PropertyRef("id", description="Tenable asset UUID.")
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last time the node was updated.",
    )
    # Core flags
    has_agent: PropertyRef = PropertyRef(
        "has_agent", description="Whether a Tenable agent is installed."
    )
    has_plugin_results: PropertyRef = PropertyRef(
        "has_plugin_results", description="Whether plugin scan results exist."
    )
    is_licensed: PropertyRef = PropertyRef(
        "is_licensed", description="Whether the asset is licensed."
    )
    is_public: PropertyRef = PropertyRef(
        "is_public", description="Whether the asset has a public IP address."
    )
    # Classification
    types: PropertyRef = PropertyRef("types", description="Asset type names.")
    system_types: PropertyRef = PropertyRef(
        "system_types", description="Asset system type names."
    )
    operating_systems: PropertyRef = PropertyRef(
        "operating_systems", description="Operating systems reported for the asset."
    )
    serial_number: PropertyRef = PropertyRef(
        "serial_number",
        extra_index=True,
        description="Hardware serial number.",
    )
    tenable_agent_days_since_active: PropertyRef = PropertyRef(
        "tenable_agent_days_since_active",
        description="Days since the Tenable agent was last active.",
    )
    # Timestamps (from asset.timestamps)
    created_at_timestamps: PropertyRef = PropertyRef(
        "created_at_timestamps", description="Asset creation timestamps."
    )
    updated_at_timestamps: PropertyRef = PropertyRef(
        "updated_at_timestamps", description="Asset update timestamps."
    )
    first_seen_timestamps: PropertyRef = PropertyRef(
        "first_seen_timestamps", description="Asset first-seen timestamps."
    )
    last_seen_timestamps: PropertyRef = PropertyRef(
        "last_seen_timestamps", description="Asset last-seen timestamps."
    )
    # Scan info (from asset.scan)
    first_scan_time: PropertyRef = PropertyRef(
        "first_scan_time", description="Timestamp of the first scan."
    )
    last_scan_time: PropertyRef = PropertyRef(
        "last_scan_time", description="Timestamp of the most recent scan."
    )
    last_authenticated_scan_date: PropertyRef = PropertyRef(
        "last_authenticated_scan_date",
        description="Timestamp of the most recent authenticated scan.",
    )
    last_licensed_scan_date: PropertyRef = PropertyRef(
        "last_licensed_scan_date",
        description="Timestamp of the most recent licensed scan.",
    )
    last_scan_id: PropertyRef = PropertyRef(
        "last_scan_id", description="ID of the most recent scan."
    )
    # Network (from asset.network): detail in TenableNetwork
    network_id: PropertyRef = PropertyRef(
        "network_id", description="Tenable network UUID."
    )
    fqdn: PropertyRef = PropertyRef(
        "fqdn", extra_index=True, description="Primary fully qualified domain name."
    )
    ipv4s: PropertyRef = PropertyRef(
        "ipv4s", description="IPv4 addresses assigned to the asset."
    )
    ipv6s: PropertyRef = PropertyRef(
        "ipv6s", description="IPv6 addresses assigned to the asset."
    )
    fqdns: PropertyRef = PropertyRef(
        "fqdns", description="Fully qualified domain names for the asset."
    )
    hostnames: PropertyRef = PropertyRef(
        "hostnames", description="Hostnames for the asset."
    )
    mac_addresses: PropertyRef = PropertyRef(
        "mac_addresses", description="MAC addresses assigned to the asset."
    )
    # Cloud identifiers: detail in TenableAssetAWS / TenableAssetAzure / TenableAssetGCP
    aws_ec2_instance_id: PropertyRef = PropertyRef(
        "aws_ec2_instance_id",
        extra_index=True,
        description="AWS EC2 instance ID.",
    )
    azure_vm_id: PropertyRef = PropertyRef(
        "azure_vm_id", extra_index=True, description="Azure virtual machine ID."
    )
    gcp_instance_id: PropertyRef = PropertyRef(
        "gcp_instance_id", extra_index=True, description="GCP instance ID."
    )
    # Ratings (from asset.ratings)
    acr_score: PropertyRef = PropertyRef(
        "acr_score", description="Asset Criticality Rating score."
    )
    aes_score: PropertyRef = PropertyRef(
        "aes_score", description="Asset Exposure Score."
    )


@dataclass(frozen=True)
class TenableAssetToTenantRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


# (:TenableTenant)-[:RESOURCE]->(:TenableAsset)
@dataclass(frozen=True)
class TenableAssetToTenantRel(CartographyRelSchema):
    """Links a Tenable tenant to one of its assets."""

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
    """Links a Tenable asset to its logical network."""

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
    """Links a Tenable asset to its AWS details."""

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
    """Links a Tenable asset to its Azure details."""

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
    """Links a Tenable asset to its GCP details."""

    target_node_label: str = "TenableAssetGCP"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("gcp_instance_id")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "HAS_GCP_INFO"
    properties: TenableAssetToGCPRelProperties = TenableAssetToGCPRelProperties()


@dataclass(frozen=True)
class TenableAssetSchema(CartographyNodeSchema):
    """An asset discovered and tracked by Tenable."""

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

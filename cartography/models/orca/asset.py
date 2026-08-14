from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.relationships import CartographyRelProperties
from cartography.models.core.relationships import CartographyRelSchema
from cartography.models.core.relationships import LinkDirection
from cartography.models.core.relationships import make_target_node_matcher
from cartography.models.core.relationships import TargetNodeMatcher


@dataclass(frozen=True)
class OrcaAssetNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "id",
        description="Stable Orca inventory identifier for the asset.",
    )
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp when this Orca asset was last seen.",
    )
    organization_id: PropertyRef = PropertyRef(
        "ORCA_ORGANIZATION_ID",
        set_in_kwargs=True,
        extra_index=True,
        description="Identifier of the Orca organization that owns this asset.",
    )
    orca_id: PropertyRef = PropertyRef(
        "orca_id",
        extra_index=True,
        description="Raw Orca inventory identifier for the asset.",
    )
    asset_unique_id: PropertyRef = PropertyRef(
        "asset_unique_id",
        extra_index=True,
        description="Orca asset identifier used to correlate equivalent inventory records.",
    )
    group_unique_id: PropertyRef = PropertyRef(
        "group_unique_id",
        description="Orca identifier for the group containing this asset.",
    )
    cluster_unique_id: PropertyRef = PropertyRef(
        "cluster_unique_id",
        description="Orca identifier for the cluster containing this asset.",
    )
    name: PropertyRef = PropertyRef(
        "name",
        extra_index=True,
        description="Human-readable asset name reported by Orca.",
    )
    asset_type: PropertyRef = PropertyRef(
        "asset_type",
        extra_index=True,
        description="Orca inventory type for the asset.",
    )
    category: PropertyRef = PropertyRef(
        "category",
        extra_index=True,
        description="High-level Orca asset category.",
    )
    subcategory: PropertyRef = PropertyRef(
        "subcategory",
        extra_index=True,
        description="Detailed Orca asset subcategory.",
    )
    cloud_provider: PropertyRef = PropertyRef(
        "cloud_provider",
        extra_index=True,
        description="Cloud platform that hosts the asset.",
    )
    cloud_account_id: PropertyRef = PropertyRef(
        "cloud_account_id",
        extra_index=True,
        description="Provider-native account, subscription, or project identifier.",
    )
    cloud_account_name: PropertyRef = PropertyRef(
        "cloud_account_name",
        description="Display name of the cloud account containing the asset.",
    )
    region: PropertyRef = PropertyRef(
        "region",
        extra_index=True,
        description="Cloud region containing the asset.",
    )
    zones: PropertyRef = PropertyRef(
        "zones",
        description="Cloud availability zone names associated with the asset.",
    )
    provider_id: PropertyRef = PropertyRef(
        "provider_id",
        extra_index=True,
        description="Provider-native resource identifier reported by Orca.",
    )
    arn: PropertyRef = PropertyRef(
        "arn",
        extra_index=True,
        description="Amazon Resource Name reported for an AWS asset, when available.",
    )
    state: PropertyRef = PropertyRef(
        "state",
        extra_index=True,
        description="Provider lifecycle state reported for the asset.",
    )
    exposure: PropertyRef = PropertyRef(
        "exposure",
        extra_index=True,
        description="Orca exposure classification for the asset.",
    )
    risk_level: PropertyRef = PropertyRef(
        "risk_level",
        extra_index=True,
        description="Orca risk-level classification for the asset.",
    )
    orca_score: PropertyRef = PropertyRef(
        "orca_score",
        description="Contextual risk score assigned to the asset by Orca.",
    )
    console_url: PropertyRef = PropertyRef(
        "console_url",
        description="URL for the asset in the Orca console.",
    )
    tags: PropertyRef = PropertyRef(
        "tags",
        description="Sorted key=value tags associated with the asset in Orca.",
    )
    first_seen: PropertyRef = PropertyRef(
        "first_seen",
        description="Timestamp when Orca first observed the asset.",
    )
    last_seen: PropertyRef = PropertyRef(
        "last_seen",
        description="Timestamp when Orca most recently observed the asset.",
    )
    creation_time: PropertyRef = PropertyRef(
        "creation_time",
        description="Provider creation timestamp for the asset.",
    )


@dataclass(frozen=True)
class OrcaAssetToOrganizationRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp when Orca last reported this ownership relationship.",
    )


@dataclass(frozen=True)
class OrcaAssetToOrganizationRel(CartographyRelSchema):
    """Links an Orca organization to one of its inventory assets."""

    target_node_label: str = "OrcaOrganization"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {
            "id": PropertyRef(
                "ORCA_ORGANIZATION_ID",
                set_in_kwargs=True,
                description="Identifier of the owning Orca organization.",
            ),
        },
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: OrcaAssetToOrganizationRelProperties = (
        OrcaAssetToOrganizationRelProperties()
    )


@dataclass(frozen=True)
class OrcaAssetSchema(CartographyNodeSchema):
    """A cloud or workload asset represented in Orca's inventory."""

    label: str = "OrcaAsset"
    properties: OrcaAssetNodeProperties = OrcaAssetNodeProperties()
    sub_resource_relationship: OrcaAssetToOrganizationRel = OrcaAssetToOrganizationRel()

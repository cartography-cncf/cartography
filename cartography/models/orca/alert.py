from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.nodes import ExtraNodeLabels
from cartography.models.core.relationships import CartographyRelProperties
from cartography.models.core.relationships import CartographyRelSchema
from cartography.models.core.relationships import LinkDirection
from cartography.models.core.relationships import make_target_node_matcher
from cartography.models.core.relationships import TargetNodeMatcher
from cartography.models.ontology.labels import SECURITY_ISSUE


@dataclass(frozen=True)
class OrcaAlertNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "id",
        description="Stable organization-scoped identifier for the Orca alert.",
    )
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp when this Orca alert was last seen.",
    )
    organization_id: PropertyRef = PropertyRef(
        "ORCA_ORGANIZATION_ID",
        set_in_kwargs=True,
        extra_index=True,
        description="Identifier of the Orca organization that owns this alert.",
    )
    orca_id: PropertyRef = PropertyRef(
        "orca_id",
        extra_index=True,
        description="Raw Orca AlertId value.",
    )
    title: PropertyRef = PropertyRef(
        "title",
        description="Human-readable Orca alert title.",
    )
    details: PropertyRef = PropertyRef(
        "details",
        description="Detailed explanation of the security issue from Orca.",
    )
    severity: PropertyRef = PropertyRef(
        "severity",
        extra_index=True,
        description="Raw Orca alert severity.",
    )
    category: PropertyRef = PropertyRef(
        "category",
        extra_index=True,
        description="Orca alert category.",
    )
    alert_type: PropertyRef = PropertyRef(
        "alert_type",
        extra_index=True,
        description="Orca alert type.",
    )
    orca_score: PropertyRef = PropertyRef(
        "orca_score",
        description="Contextual risk score assigned to the alert by Orca.",
    )
    status: PropertyRef = PropertyRef(
        "status",
        extra_index=True,
        description="Raw Orca alert workflow status.",
    )
    created_at: PropertyRef = PropertyRef(
        "created_at",
        description="Timestamp when Orca created the alert.",
    )
    last_seen: PropertyRef = PropertyRef(
        "last_seen",
        description="Timestamp when Orca most recently observed the alert.",
    )
    console_url: PropertyRef = PropertyRef(
        "console_url",
        description="URL for the alert in the Orca console.",
    )
    cve_ids: PropertyRef = PropertyRef(
        "cve_ids",
        description="CVE identifiers referenced by the alert.",
    )
    target_orca_inventory_id: PropertyRef = PropertyRef(
        "target_orca_inventory_id",
        extra_index=True,
        description="Orca inventory identifier associated with the alert target.",
    )
    target_orca_asset_unique_id: PropertyRef = PropertyRef(
        "target_orca_asset_unique_id",
        extra_index=True,
        description="Orca AssetUniqueId associated with the alert target.",
    )
    target_provider_id: PropertyRef = PropertyRef(
        "target_provider_id",
        extra_index=True,
        description="Provider-native identifier associated with the alert target.",
    )
    target_arn: PropertyRef = PropertyRef(
        "target_arn",
        extra_index=True,
        description="Amazon Resource Name associated with the alert target.",
    )
    target_cloud_provider: PropertyRef = PropertyRef(
        "target_cloud_provider",
        extra_index=True,
        description="Cloud provider associated with the alert target.",
    )
    target_cloud_account_id: PropertyRef = PropertyRef(
        "target_cloud_account_id",
        extra_index=True,
        description="Provider-native account, subscription, or project identifier associated with the alert target.",
    )
    target_region: PropertyRef = PropertyRef(
        "target_region",
        description="Cloud region associated with the alert target.",
    )
    target_name: PropertyRef = PropertyRef(
        "target_name",
        description="Display name reported for the alert target.",
    )
    target_type: PropertyRef = PropertyRef(
        "target_type",
        description="Orca resource type reported for the alert target.",
    )


@dataclass(frozen=True)
class OrcaAlertToOrganizationRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp when Orca last reported this ownership relationship.",
    )


@dataclass(frozen=True)
class OrcaAlertToOrganizationRel(CartographyRelSchema):
    """Links an Orca organization to one of its alerts."""

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
    properties: OrcaAlertToOrganizationRelProperties = (
        OrcaAlertToOrganizationRelProperties()
    )


@dataclass(frozen=True)
class OrcaAlertSchema(CartographyNodeSchema):
    """A security issue reported and prioritized by Orca."""

    label: str = "OrcaAlert"
    properties: OrcaAlertNodeProperties = OrcaAlertNodeProperties()
    sub_resource_relationship: OrcaAlertToOrganizationRel = OrcaAlertToOrganizationRel()
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels([SECURITY_ISSUE])

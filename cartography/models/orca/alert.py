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
from cartography.models.ontology.labels import SECURITY_ISSUE


@dataclass(frozen=True)
class OrcaAlertNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "id",
        description="Stable Orca AlertId identifier.",
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
    asset_id: PropertyRef = PropertyRef(
        "asset_id",
        extra_index=True,
        description="Stable identifier of the affected Orca asset.",
    )
    asset_name: PropertyRef = PropertyRef(
        "asset_name",
        description="Fallback display name of the affected asset from the alert.",
    )
    asset_type: PropertyRef = PropertyRef(
        "asset_type",
        extra_index=True,
        description="Fallback Orca type of the affected asset from the alert.",
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
class OrcaAlertToAssetRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp when Orca last reported the affected asset.",
    )


@dataclass(frozen=True)
class OrcaAlertToAssetRel(CartographyRelSchema):
    """Links an Orca alert to the asset that it affects."""

    target_node_label: str = "OrcaAsset"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {
            "id": PropertyRef(
                "asset_id",
                description="Stable identifier of the affected Orca asset.",
            ),
            "lastupdated": PropertyRef(
                "lastupdated",
                set_in_kwargs=True,
                description="Current sync timestamp required for an asset match.",
            ),
        },
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "AFFECTS"
    properties: OrcaAlertToAssetRelProperties = OrcaAlertToAssetRelProperties()


@dataclass(frozen=True)
class OrcaAlertSchema(CartographyNodeSchema):
    """A security issue reported and prioritized by Orca."""

    label: str = "OrcaAlert"
    properties: OrcaAlertNodeProperties = OrcaAlertNodeProperties()
    sub_resource_relationship: OrcaAlertToOrganizationRel = OrcaAlertToOrganizationRel()
    other_relationships: OtherRelationships = OtherRelationships(
        [OrcaAlertToAssetRel()],
    )
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels([SECURITY_ISSUE])

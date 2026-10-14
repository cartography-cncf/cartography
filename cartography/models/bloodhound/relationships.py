"""Relationships between AD objects, built from BloodHound collector output.

Each BloodHound edge kind gets its own relationship label so path queries can
traverse specific abuse primitives. Every edge is a MatchLink between nodes the
import already created, scoped to the domain whose object declared it.
"""

from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.relationships import CartographyRelProperties
from cartography.models.core.relationships import CartographyRelSchema
from cartography.models.core.relationships import LinkDirection
from cartography.models.core.relationships import make_source_node_matcher
from cartography.models.core.relationships import make_target_node_matcher
from cartography.models.core.relationships import SourceNodeMatcher
from cartography.models.core.relationships import TargetNodeMatcher


@dataclass(frozen=True)
class ADEdgeMatchLinkProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    _sub_resource_label: PropertyRef = PropertyRef(
        "_sub_resource_label",
        set_in_kwargs=True,
    )
    _sub_resource_id: PropertyRef = PropertyRef(
        "_sub_resource_id",
        set_in_kwargs=True,
    )
    source_uri: PropertyRef = PropertyRef(
        "source_uri",
        description="URI of the collector output file the edge was read from.",
    )
    collected_at: PropertyRef = PropertyRef(
        "collected_at",
        description=(
            "Collection time from the collector output, as an ISO 8601 timestamp. "
            "SharpHound writes the collector host's local time without an offset."
        ),
    )
    collector_version: PropertyRef = PropertyRef(
        "collector_version",
        description="Version of the collector that produced the output.",
    )


@dataclass(frozen=True)
class ADACLMatchLinkProperties(ADEdgeMatchLinkProperties):
    is_inherited: PropertyRef = PropertyRef(
        "is_inherited",
        description=(
            "Whether the right comes only from ACEs inherited from a parent "
            "container. False when any ACE grants it on the object itself."
        ),
    )


@dataclass(frozen=True)
# (:ADObject)-[:MEMBER_OF]->(:ADGroup)
class ADMemberOfMatchLink(CartographyRelSchema):
    """Membership of a user, computer or group in an AD group, including primary group membership."""

    source_node_label: str = "ADObject"
    source_node_matcher: SourceNodeMatcher = make_source_node_matcher(
        {"id": PropertyRef("source_id")},
    )
    target_node_label: str = "ADGroup"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("target_id")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "MEMBER_OF"
    properties: ADEdgeMatchLinkProperties = ADEdgeMatchLinkProperties()


@dataclass(frozen=True)
# (:ADObject)-[:CONTAINS]->(:ADObject)
class ADContainsMatchLink(CartographyRelSchema):
    """A domain, OU or container directly holds the child object in the directory tree."""

    source_node_label: str = "ADObject"
    source_node_matcher: SourceNodeMatcher = make_source_node_matcher(
        {"id": PropertyRef("source_id")},
    )
    target_node_label: str = "ADObject"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("target_id")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "CONTAINS"
    properties: ADEdgeMatchLinkProperties = ADEdgeMatchLinkProperties()


@dataclass(frozen=True)
class ADGPLinkMatchLinkProperties(ADEdgeMatchLinkProperties):
    enforced: PropertyRef = PropertyRef(
        "enforced",
        description="Whether the link is enforced, so OUs that block inheritance still apply it.",
    )


@dataclass(frozen=True)
# (:ADGPO)-[:GP_LINK]->(:ADObject)
class ADGPLinkMatchLink(CartographyRelSchema):
    """A group policy object is linked to a domain or OU and applies to the objects under it."""

    source_node_label: str = "ADGPO"
    source_node_matcher: SourceNodeMatcher = make_source_node_matcher(
        {"id": PropertyRef("source_id")},
    )
    target_node_label: str = "ADObject"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("target_id")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "GP_LINK"
    properties: ADGPLinkMatchLinkProperties = ADGPLinkMatchLinkProperties()


@dataclass(frozen=True)
class ADTrustMatchLinkProperties(ADEdgeMatchLinkProperties):
    trust_type: PropertyRef = PropertyRef(
        "trust_type",
        description="Trust type as SharpHound reports it, such as `ParentChild`, `TreeRoot`, `Shortcut`, `External`, `Forest`, `Realm` or `Unknown`.",
    )
    is_transitive: PropertyRef = PropertyRef(
        "is_transitive",
        description="Whether the trust is transitive.",
    )
    sid_filtering_enabled: PropertyRef = PropertyRef(
        "sid_filtering_enabled",
        description="Whether SID filtering is enforced on the trust.",
    )
    tgt_delegation_enabled: PropertyRef = PropertyRef(
        "tgt_delegation_enabled",
        description="Whether TGT delegation is allowed across the trust.",
    )
    trust_attributes: PropertyRef = PropertyRef(
        "trust_attributes",
        description="Raw `trustAttributes` bitmask.",
    )


@dataclass(frozen=True)
# (:ADDomain)-[:SAME_FOREST_TRUST]->(:ADDomain)
class ADSameForestTrustMatchLink(CartographyRelSchema):
    """The source domain trusts the target domain in the same forest (`ParentChild`, `TreeRoot` or `CrossLink`), so the target's principals can authenticate in the source."""

    source_node_label: str = "ADDomain"
    source_node_matcher: SourceNodeMatcher = make_source_node_matcher(
        {"id": PropertyRef("source_id")},
    )
    target_node_label: str = "ADDomain"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("target_id")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "SAME_FOREST_TRUST"
    properties: ADTrustMatchLinkProperties = ADTrustMatchLinkProperties()


@dataclass(frozen=True)
# (:ADDomain)-[:CROSS_FOREST_TRUST]->(:ADDomain)
class ADCrossForestTrustMatchLink(CartographyRelSchema):
    """The source domain trusts the target domain across forests (any trust type other than `ParentChild`, `TreeRoot` or `CrossLink`), so the target's principals can authenticate in the source."""

    source_node_label: str = "ADDomain"
    source_node_matcher: SourceNodeMatcher = make_source_node_matcher(
        {"id": PropertyRef("source_id")},
    )
    target_node_label: str = "ADDomain"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("target_id")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "CROSS_FOREST_TRUST"
    properties: ADTrustMatchLinkProperties = ADTrustMatchLinkProperties()

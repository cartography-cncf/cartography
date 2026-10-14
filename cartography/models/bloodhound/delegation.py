"""Kerberos delegation and SID history edges read from SharpHound's user and computer data."""

from dataclasses import dataclass

from cartography.models.bloodhound.relationships import ADEdgeMatchLinkProperties
from cartography.models.core.common import PropertyRef
from cartography.models.core.relationships import CartographyRelSchema
from cartography.models.core.relationships import LinkDirection
from cartography.models.core.relationships import make_source_node_matcher
from cartography.models.core.relationships import make_target_node_matcher
from cartography.models.core.relationships import SourceNodeMatcher
from cartography.models.core.relationships import TargetNodeMatcher


@dataclass(frozen=True)
# (:ADObject)-[:ALLOWED_TO_DELEGATE]->(:ADObject)
class ADAllowedToDelegateMatchLink(CartographyRelSchema):
    """The account is trusted for constrained delegation to services on the target (`msDS-AllowedToDelegateTo`)."""

    source_node_label: str = "ADObject"
    source_node_matcher: SourceNodeMatcher = make_source_node_matcher(
        {"id": PropertyRef("source_id")},
    )
    target_node_label: str = "ADObject"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("target_id")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "ALLOWED_TO_DELEGATE"
    properties: ADEdgeMatchLinkProperties = ADEdgeMatchLinkProperties()


@dataclass(frozen=True)
# (:ADObject)-[:ALLOWED_TO_ACT]->(:ADComputer)
class ADAllowedToActMatchLink(CartographyRelSchema):
    """The principal may act on behalf of other users against the computer, through resource-based constrained delegation (`msDS-AllowedToActOnBehalfOfOtherIdentity`)."""

    source_node_label: str = "ADObject"
    source_node_matcher: SourceNodeMatcher = make_source_node_matcher(
        {"id": PropertyRef("source_id")},
    )
    target_node_label: str = "ADComputer"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("target_id")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "ALLOWED_TO_ACT"
    properties: ADEdgeMatchLinkProperties = ADEdgeMatchLinkProperties()


@dataclass(frozen=True)
# (:ADObject)-[:HAS_SID_HISTORY]->(:ADObject)
class ADHasSidHistoryMatchLink(CartographyRelSchema):
    """The account's SID history holds the target's SID, so the account is granted the target's access."""

    source_node_label: str = "ADObject"
    source_node_matcher: SourceNodeMatcher = make_source_node_matcher(
        {"id": PropertyRef("source_id")},
    )
    target_node_label: str = "ADObject"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("target_id")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "HAS_SID_HISTORY"
    properties: ADEdgeMatchLinkProperties = ADEdgeMatchLinkProperties()

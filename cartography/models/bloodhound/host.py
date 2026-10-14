"""Host access edges read from SharpHound's computer data.

Local group membership comes from the computer itself or from group policy
that assigns local group members. Sessions come from the session, privileged
session and registry session lists.
"""

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
# (:ADObject)-[:ADMIN_TO]->(:ADComputer)
class ADAdminToMatchLink(CartographyRelSchema):
    """The principal is a member of the computer's local Administrators group (RID 544)."""

    source_node_label: str = "ADObject"
    source_node_matcher: SourceNodeMatcher = make_source_node_matcher(
        {"id": PropertyRef("source_id")},
    )
    target_node_label: str = "ADComputer"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("target_id")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "ADMIN_TO"
    properties: ADEdgeMatchLinkProperties = ADEdgeMatchLinkProperties()


@dataclass(frozen=True)
# (:ADObject)-[:CAN_RDP]->(:ADComputer)
class ADCanRdpMatchLink(CartographyRelSchema):
    """The principal is a member of the computer's local Remote Desktop Users group (RID 555) and, when user rights were collected, holds the remote interactive logon right."""

    source_node_label: str = "ADObject"
    source_node_matcher: SourceNodeMatcher = make_source_node_matcher(
        {"id": PropertyRef("source_id")},
    )
    target_node_label: str = "ADComputer"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("target_id")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "CAN_RDP"
    properties: ADEdgeMatchLinkProperties = ADEdgeMatchLinkProperties()


@dataclass(frozen=True)
# (:ADObject)-[:CAN_PS_REMOTE]->(:ADComputer)
class ADCanPsRemoteMatchLink(CartographyRelSchema):
    """The principal is a member of the computer's local Remote Management Users group (RID 580)."""

    source_node_label: str = "ADObject"
    source_node_matcher: SourceNodeMatcher = make_source_node_matcher(
        {"id": PropertyRef("source_id")},
    )
    target_node_label: str = "ADComputer"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("target_id")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "CAN_PS_REMOTE"
    properties: ADEdgeMatchLinkProperties = ADEdgeMatchLinkProperties()


@dataclass(frozen=True)
# (:ADComputer)-[:HAS_SESSION]->(:ADUser)
class ADHasSessionMatchLink(CartographyRelSchema):
    """The user had a logon session on the computer when SharpHound collected it."""

    source_node_label: str = "ADComputer"
    source_node_matcher: SourceNodeMatcher = make_source_node_matcher(
        {"id": PropertyRef("source_id")},
    )
    target_node_label: str = "ADUser"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("target_id")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "HAS_SESSION"
    properties: ADEdgeMatchLinkProperties = ADEdgeMatchLinkProperties()

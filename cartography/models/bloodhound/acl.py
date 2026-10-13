"""Permission edges read from the access control entries (ACEs) SharpHound collects.

The source principal holds the right over the target object. ``is_inherited``
records whether the ACE was inherited from a parent container.
"""

from dataclasses import dataclass

from cartography.models.bloodhound.relationships import ADACLMatchLinkProperties
from cartography.models.bloodhound.relationships import ADEdgeMatchLinkProperties
from cartography.models.core.common import PropertyRef
from cartography.models.core.relationships import CartographyRelSchema
from cartography.models.core.relationships import LinkDirection
from cartography.models.core.relationships import make_source_node_matcher
from cartography.models.core.relationships import make_target_node_matcher
from cartography.models.core.relationships import SourceNodeMatcher
from cartography.models.core.relationships import TargetNodeMatcher


@dataclass(frozen=True)
# (:ADObject)-[:GENERIC_ALL]->(:ADObject)
class ADGenericAllMatchLink(CartographyRelSchema):
    """The principal has full control of the target object."""

    source_node_label: str = "ADObject"
    source_node_matcher: SourceNodeMatcher = make_source_node_matcher(
        {"id": PropertyRef("source_id")},
    )
    target_node_label: str = "ADObject"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("target_id")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "GENERIC_ALL"
    properties: ADACLMatchLinkProperties = ADACLMatchLinkProperties()


@dataclass(frozen=True)
# (:ADObject)-[:GENERIC_WRITE]->(:ADObject)
class ADGenericWriteMatchLink(CartographyRelSchema):
    """The principal can write any unprotected attribute of the target object."""

    source_node_label: str = "ADObject"
    source_node_matcher: SourceNodeMatcher = make_source_node_matcher(
        {"id": PropertyRef("source_id")},
    )
    target_node_label: str = "ADObject"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("target_id")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "GENERIC_WRITE"
    properties: ADACLMatchLinkProperties = ADACLMatchLinkProperties()


@dataclass(frozen=True)
# (:ADObject)-[:WRITE_DACL]->(:ADObject)
class ADWriteDaclMatchLink(CartographyRelSchema):
    """The principal can modify the target object's DACL, and so grant itself any right on it."""

    source_node_label: str = "ADObject"
    source_node_matcher: SourceNodeMatcher = make_source_node_matcher(
        {"id": PropertyRef("source_id")},
    )
    target_node_label: str = "ADObject"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("target_id")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "WRITE_DACL"
    properties: ADACLMatchLinkProperties = ADACLMatchLinkProperties()


@dataclass(frozen=True)
# (:ADObject)-[:WRITE_OWNER]->(:ADObject)
class ADWriteOwnerMatchLink(CartographyRelSchema):
    """The principal can make itself the owner of the target object."""

    source_node_label: str = "ADObject"
    source_node_matcher: SourceNodeMatcher = make_source_node_matcher(
        {"id": PropertyRef("source_id")},
    )
    target_node_label: str = "ADObject"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("target_id")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "WRITE_OWNER"
    properties: ADACLMatchLinkProperties = ADACLMatchLinkProperties()


@dataclass(frozen=True)
# (:ADObject)-[:OWNS]->(:ADObject)
class ADOwnsMatchLink(CartographyRelSchema):
    """The principal owns the target object, which implicitly lets it modify the object's DACL."""

    source_node_label: str = "ADObject"
    source_node_matcher: SourceNodeMatcher = make_source_node_matcher(
        {"id": PropertyRef("source_id")},
    )
    target_node_label: str = "ADObject"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("target_id")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "OWNS"
    properties: ADACLMatchLinkProperties = ADACLMatchLinkProperties()


@dataclass(frozen=True)
# (:ADObject)-[:FORCE_CHANGE_PASSWORD]->(:ADObject)
class ADForceChangePasswordMatchLink(CartographyRelSchema):
    """The principal can reset the target user's password without knowing the current one."""

    source_node_label: str = "ADObject"
    source_node_matcher: SourceNodeMatcher = make_source_node_matcher(
        {"id": PropertyRef("source_id")},
    )
    target_node_label: str = "ADObject"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("target_id")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "FORCE_CHANGE_PASSWORD"
    properties: ADACLMatchLinkProperties = ADACLMatchLinkProperties()


@dataclass(frozen=True)
# (:ADObject)-[:ADD_MEMBER]->(:ADObject)
class ADAddMemberMatchLink(CartographyRelSchema):
    """The principal can add any principal to the target group."""

    source_node_label: str = "ADObject"
    source_node_matcher: SourceNodeMatcher = make_source_node_matcher(
        {"id": PropertyRef("source_id")},
    )
    target_node_label: str = "ADObject"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("target_id")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "ADD_MEMBER"
    properties: ADACLMatchLinkProperties = ADACLMatchLinkProperties()


@dataclass(frozen=True)
# (:ADObject)-[:ALL_EXTENDED_RIGHTS]->(:ADObject)
class ADAllExtendedRightsMatchLink(CartographyRelSchema):
    """The principal holds every extended right on the target object, such as resetting a password or reading a LAPS password."""

    source_node_label: str = "ADObject"
    source_node_matcher: SourceNodeMatcher = make_source_node_matcher(
        {"id": PropertyRef("source_id")},
    )
    target_node_label: str = "ADObject"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("target_id")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "ALL_EXTENDED_RIGHTS"
    properties: ADACLMatchLinkProperties = ADACLMatchLinkProperties()


@dataclass(frozen=True)
# (:ADObject)-[:ADD_KEY_CREDENTIAL_LINK]->(:ADObject)
class ADAddKeyCredentialLinkMatchLink(CartographyRelSchema):
    """The principal can write the target's `msDS-KeyCredentialLink` attribute and so add a key credential to it."""

    source_node_label: str = "ADObject"
    source_node_matcher: SourceNodeMatcher = make_source_node_matcher(
        {"id": PropertyRef("source_id")},
    )
    target_node_label: str = "ADObject"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("target_id")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "ADD_KEY_CREDENTIAL_LINK"
    properties: ADACLMatchLinkProperties = ADACLMatchLinkProperties()


@dataclass(frozen=True)
# (:ADObject)-[:READ_LAPS_PASSWORD]->(:ADObject)
class ADReadLapsPasswordMatchLink(CartographyRelSchema):
    """The principal can read the LAPS-managed local administrator password of the target computer."""

    source_node_label: str = "ADObject"
    source_node_matcher: SourceNodeMatcher = make_source_node_matcher(
        {"id": PropertyRef("source_id")},
    )
    target_node_label: str = "ADObject"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("target_id")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "READ_LAPS_PASSWORD"
    properties: ADACLMatchLinkProperties = ADACLMatchLinkProperties()


@dataclass(frozen=True)
# (:ADObject)-[:READ_GMSA_PASSWORD]->(:ADObject)
class ADReadGmsaPasswordMatchLink(CartographyRelSchema):
    """The principal can read the password of the target group managed service account."""

    source_node_label: str = "ADObject"
    source_node_matcher: SourceNodeMatcher = make_source_node_matcher(
        {"id": PropertyRef("source_id")},
    )
    target_node_label: str = "ADObject"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("target_id")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "READ_GMSA_PASSWORD"
    properties: ADACLMatchLinkProperties = ADACLMatchLinkProperties()


@dataclass(frozen=True)
# (:ADObject)-[:ADD_SELF]->(:ADObject)
class ADAddSelfMatchLink(CartographyRelSchema):
    """The principal can add itself to the target group."""

    source_node_label: str = "ADObject"
    source_node_matcher: SourceNodeMatcher = make_source_node_matcher(
        {"id": PropertyRef("source_id")},
    )
    target_node_label: str = "ADObject"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("target_id")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "ADD_SELF"
    properties: ADACLMatchLinkProperties = ADACLMatchLinkProperties()


@dataclass(frozen=True)
# (:ADObject)-[:WRITE_SPN]->(:ADObject)
class ADWriteSpnMatchLink(CartographyRelSchema):
    """The principal can write the target's `servicePrincipalName` attribute."""

    source_node_label: str = "ADObject"
    source_node_matcher: SourceNodeMatcher = make_source_node_matcher(
        {"id": PropertyRef("source_id")},
    )
    target_node_label: str = "ADObject"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("target_id")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "WRITE_SPN"
    properties: ADACLMatchLinkProperties = ADACLMatchLinkProperties()


@dataclass(frozen=True)
# (:ADObject)-[:DC_SYNC]->(:ADDomain)
class ADDCSyncMatchLink(CartographyRelSchema):
    """The principal holds both the GetChanges and GetChangesAll replication rights on the domain, which allows DCSync. Derived from the domain's ACEs."""

    source_node_label: str = "ADObject"
    source_node_matcher: SourceNodeMatcher = make_source_node_matcher(
        {"id": PropertyRef("source_id")},
    )
    target_node_label: str = "ADDomain"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("target_id")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "DC_SYNC"
    properties: ADEdgeMatchLinkProperties = ADEdgeMatchLinkProperties()

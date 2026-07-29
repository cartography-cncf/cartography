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
class UbuntuSecurityNoticeNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "id", description="USN identifier, for example `USN-6600-1`."
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    title: PropertyRef = PropertyRef(
        "title", description="Title of the security notice."
    )
    summary: PropertyRef = PropertyRef(
        "summary", description="Brief summary of the notice."
    )
    description: PropertyRef = PropertyRef(
        "description", description="Full description of the notice."
    )
    published: PropertyRef = PropertyRef(
        "published", description="Date the notice was published."
    )
    notice_type: PropertyRef = PropertyRef(
        "notice_type", description="Type of notice, for example USN."
    )
    instructions: PropertyRef = PropertyRef(
        "instructions", description="Remediation instructions."
    )
    is_hidden: PropertyRef = PropertyRef(
        "is_hidden", description="Whether Ubuntu marks this notice as hidden."
    )


@dataclass(frozen=True)
class UbuntuNoticeToUbuntuCVEFeedRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class UbuntuNoticeToUbuntuCVEFeedRel(CartographyRelSchema):
    """Links the Ubuntu Security feed to a notice it publishes."""

    target_node_label: str = "UbuntuCVEFeed"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("FEED_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: UbuntuNoticeToUbuntuCVEFeedRelProperties = (
        UbuntuNoticeToUbuntuCVEFeedRelProperties()
    )


@dataclass(frozen=True)
class UbuntuNoticeToUbuntuCVERelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class UbuntuNoticeToUbuntuCVERel(CartographyRelSchema):
    """Links a security notice to each CVE it remediates."""

    target_node_label: str = "UbuntuCVE"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("cves_ids", one_to_many=True)},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "ADDRESSES"
    properties: UbuntuNoticeToUbuntuCVERelProperties = (
        UbuntuNoticeToUbuntuCVERelProperties()
    )


@dataclass(frozen=True)
class UbuntuSecurityNoticeSchema(CartographyNodeSchema):
    """A Ubuntu Security Notice (USN) from the
    [Ubuntu Security API](https://ubuntu.com/security/notices)."""

    label: str = "UbuntuSecurityNotice"
    properties: UbuntuSecurityNoticeNodeProperties = (
        UbuntuSecurityNoticeNodeProperties()
    )
    sub_resource_relationship: UbuntuNoticeToUbuntuCVEFeedRel = (
        UbuntuNoticeToUbuntuCVEFeedRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        rels=[
            UbuntuNoticeToUbuntuCVERel(),
        ],
    )

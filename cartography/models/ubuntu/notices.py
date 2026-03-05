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
    id: PropertyRef = PropertyRef("id")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    title: PropertyRef = PropertyRef("title")
    summary: PropertyRef = PropertyRef("summary")
    description: PropertyRef = PropertyRef("description")
    published: PropertyRef = PropertyRef("published")
    notice_type: PropertyRef = PropertyRef("notice_type")
    instructions: PropertyRef = PropertyRef("instructions")
    is_hidden: PropertyRef = PropertyRef("is_hidden")


@dataclass(frozen=True)
class UbuntuNoticeToUbuntuCVEFeedRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class UbuntuNoticeToUbuntuCVEFeedRel(CartographyRelSchema):
    """(:UbuntuSecurityNotice)<-[:RESOURCE]-(:UbuntuCVEFeed)"""

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
    """(:UbuntuSecurityNotice)-[:ADDRESSES]->(:UbuntuCVE)"""

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

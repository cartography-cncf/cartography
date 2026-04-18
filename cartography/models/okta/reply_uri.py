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
class OktaReplyUriNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id")
    uri: PropertyRef = PropertyRef("uri")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class OktaReplyUriToOktaOrganizationRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:ReplyUri)<-[:RESOURCE]-(:OktaOrganization)
class OktaReplyUriToOktaOrganizationRel(CartographyRelSchema):
    target_node_label: str = "OktaOrganization"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("OKTA_ORG_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: OktaReplyUriToOktaOrganizationRelProperties = (
        OktaReplyUriToOktaOrganizationRelProperties()
    )


@dataclass(frozen=True)
class OktaReplyUriToOktaApplicationRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:ReplyUri)<-[:REPLYURI]-(:OktaApplication)
class OktaReplyUriToOktaApplicationRel(CartographyRelSchema):
    target_node_label: str = "OktaApplication"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("application_id")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "REPLYURI"
    properties: OktaReplyUriToOktaApplicationRelProperties = (
        OktaReplyUriToOktaApplicationRelProperties()
    )


@dataclass(frozen=True)
class OktaReplyUriSchema(CartographyNodeSchema):
    label: str = "ReplyUri"
    properties: OktaReplyUriNodeProperties = OktaReplyUriNodeProperties()
    sub_resource_relationship: OktaReplyUriToOktaOrganizationRel = (
        OktaReplyUriToOktaOrganizationRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        rels=[OktaReplyUriToOktaApplicationRel()],
    )

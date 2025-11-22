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
class ReplyUriProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    uri: PropertyRef = PropertyRef("uri")


@dataclass(frozen=True)
class ReplyUriToApplicationProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:OktaApplication)-[:REPLYURI]->(:ReplyUri)
class ReplyUriToApplicationRel(CartographyRelSchema):
    target_node_label: str = "OktaApplication"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("applications", one_to_many=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "REPLYURI"
    properties: ReplyUriToApplicationProperties = ReplyUriToApplicationProperties()


@dataclass(frozen=True)
class ReplyUriSchema(CartographyNodeSchema):
    label: str = "ReplyUri"
    properties: ReplyUriProperties = ReplyUriProperties()
    other_relationships: OtherRelationships = OtherRelationships(
        [
            ReplyUriToApplicationRel(),
        ]
    )

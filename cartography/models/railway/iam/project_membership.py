"""
MatchLink for Railway project membership.

A user belongs to many projects, holding a different role in each, so the role has to live
on the edge keyed per (user, project) pair. That does not fit a plain CartographyRelSchema
on RailwayUser, which can only carry one row per node.
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
class RailwayProjectMembershipRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    role: PropertyRef = PropertyRef("role")
    _sub_resource_label: PropertyRef = PropertyRef(
        "_sub_resource_label",
        set_in_kwargs=True,
    )
    _sub_resource_id: PropertyRef = PropertyRef("_sub_resource_id", set_in_kwargs=True)


@dataclass(frozen=True)
# (:RailwayUser)-[:MEMBER_OF]->(:RailwayProject)
class RailwayUserToProjectMatchLink(CartographyRelSchema):
    source_node_label: str = "RailwayUser"
    source_node_matcher: SourceNodeMatcher = make_source_node_matcher(
        {"id": PropertyRef("user_id")},
    )
    target_node_label: str = "RailwayProject"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("project_id")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "MEMBER_OF"
    properties: RailwayProjectMembershipRelProperties = (
        RailwayProjectMembershipRelProperties()
    )

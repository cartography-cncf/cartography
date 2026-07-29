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
class DopplerProjectMembershipRelProperties(CartographyRelProperties):
    # Mandatory fields for MatchLinks
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    _sub_resource_label: PropertyRef = PropertyRef(
        "_sub_resource_label", set_in_kwargs=True
    )
    _sub_resource_id: PropertyRef = PropertyRef("_sub_resource_id", set_in_kwargs=True)

    # Business properties carried on the edge
    role: PropertyRef = PropertyRef("role")
    access_all_environments: PropertyRef = PropertyRef("access_all_environments")


@dataclass(frozen=True)
# (:DopplerWorkplaceUser)-[:MEMBER_OF]->(:DopplerProject)
class DopplerUserToProjectMatchLink(CartographyRelSchema):
    rel_label: str = "MEMBER_OF"
    direction: LinkDirection = LinkDirection.OUTWARD
    properties: DopplerProjectMembershipRelProperties = (
        DopplerProjectMembershipRelProperties()
    )
    source_node_label: str = "DopplerWorkplaceUser"
    source_node_matcher: SourceNodeMatcher = make_source_node_matcher(
        {"id": PropertyRef("slug")},
    )
    target_node_label: str = "DopplerProject"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"slug": PropertyRef("project")},
    )


@dataclass(frozen=True)
# (:DopplerGroup)-[:MEMBER_OF]->(:DopplerProject)
class DopplerGroupToProjectMatchLink(CartographyRelSchema):
    rel_label: str = "MEMBER_OF"
    direction: LinkDirection = LinkDirection.OUTWARD
    properties: DopplerProjectMembershipRelProperties = (
        DopplerProjectMembershipRelProperties()
    )
    source_node_label: str = "DopplerGroup"
    source_node_matcher: SourceNodeMatcher = make_source_node_matcher(
        {"id": PropertyRef("slug")},
    )
    target_node_label: str = "DopplerProject"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"slug": PropertyRef("project")},
    )


@dataclass(frozen=True)
# (:DopplerServiceAccount)-[:MEMBER_OF]->(:DopplerProject)
class DopplerServiceAccountToProjectMatchLink(CartographyRelSchema):
    rel_label: str = "MEMBER_OF"
    direction: LinkDirection = LinkDirection.OUTWARD
    properties: DopplerProjectMembershipRelProperties = (
        DopplerProjectMembershipRelProperties()
    )
    source_node_label: str = "DopplerServiceAccount"
    source_node_matcher: SourceNodeMatcher = make_source_node_matcher(
        {"id": PropertyRef("slug")},
    )
    target_node_label: str = "DopplerProject"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"slug": PropertyRef("project")},
    )

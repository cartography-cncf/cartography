from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.relationships import CartographyRelProperties
from cartography.models.core.relationships import CartographyRelSchema
from cartography.models.core.relationships import LinkDirection
from cartography.models.core.relationships import make_source_node_matcher
from cartography.models.core.relationships import make_target_node_matcher
from cartography.models.core.relationships import SourceNodeMatcher
from cartography.models.core.relationships import TargetNodeMatcher


@dataclass(frozen=True)
class DopplerGroupNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("slug")
    name: PropertyRef = PropertyRef("name")
    created_at: PropertyRef = PropertyRef("created_at")
    default_project_role: PropertyRef = PropertyRef("default_project_role")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class DopplerGroupToWorkplaceRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:DopplerWorkplace)-[:RESOURCE]->(:DopplerGroup)
class DopplerGroupToWorkplaceRel(CartographyRelSchema):
    target_node_label: str = "DopplerWorkplace"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("WORKPLACE_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: DopplerGroupToWorkplaceRelProperties = (
        DopplerGroupToWorkplaceRelProperties()
    )


@dataclass(frozen=True)
class DopplerGroupSchema(CartographyNodeSchema):
    label: str = "DopplerGroup"
    properties: DopplerGroupNodeProperties = DopplerGroupNodeProperties()
    sub_resource_relationship: DopplerGroupToWorkplaceRel = DopplerGroupToWorkplaceRel()


@dataclass(frozen=True)
class DopplerGroupMembershipRelProperties(CartographyRelProperties):
    # Mandatory fields for MatchLinks
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    _sub_resource_label: PropertyRef = PropertyRef(
        "_sub_resource_label", set_in_kwargs=True
    )
    _sub_resource_id: PropertyRef = PropertyRef("_sub_resource_id", set_in_kwargs=True)


@dataclass(frozen=True)
# (:DopplerWorkplaceUser)-[:MEMBER_OF]->(:DopplerGroup)
class DopplerGroupMembershipMatchLink(CartographyRelSchema):
    rel_label: str = "MEMBER_OF"
    direction: LinkDirection = LinkDirection.OUTWARD
    properties: DopplerGroupMembershipRelProperties = (
        DopplerGroupMembershipRelProperties()
    )
    source_node_label: str = "DopplerWorkplaceUser"
    source_node_matcher: SourceNodeMatcher = make_source_node_matcher(
        {"id": PropertyRef("user_id")},
    )
    target_node_label: str = "DopplerGroup"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("group_slug")},
    )

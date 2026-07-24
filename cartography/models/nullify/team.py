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
class NullifyTeamNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    name: PropertyRef = PropertyRef("name", extra_index=True)
    slug: PropertyRef = PropertyRef("slug", extra_index=True)
    privacy: PropertyRef = PropertyRef("privacy")
    num_members: PropertyRef = PropertyRef("numMembers")


@dataclass(frozen=True)
class NullifyTeamToTenantRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:NullifyTenant)-[:RESOURCE]->(:NullifyTeam)
class NullifyTeamToTenantRel(CartographyRelSchema):
    target_node_label: str = "NullifyTenant"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("TENANT_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: NullifyTeamToTenantRelProperties = NullifyTeamToTenantRelProperties()


@dataclass(frozen=True)
class NullifyTeamToRepositoryRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:NullifyTeam)-[:OWNS]->(:NullifyRepository)
class NullifyTeamToRepositoryRel(CartographyRelSchema):
    target_node_label: str = "NullifyRepository"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"repository_id": PropertyRef("repositoryIds", one_to_many=True)},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "OWNS"
    properties: NullifyTeamToRepositoryRelProperties = (
        NullifyTeamToRepositoryRelProperties()
    )


@dataclass(frozen=True)
class NullifyTeamToMemberRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:NullifyUser)-[:MEMBER_OF]->(:NullifyTeam)
class NullifyTeamToMemberRel(CartographyRelSchema):
    target_node_label: str = "NullifyUser"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("memberIds", one_to_many=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "MEMBER_OF"
    properties: NullifyTeamToMemberRelProperties = NullifyTeamToMemberRelProperties()


@dataclass(frozen=True)
class NullifyTeamToLeadRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:NullifyUser)-[:LEADS]->(:NullifyTeam)
class NullifyTeamToLeadRel(CartographyRelSchema):
    target_node_label: str = "NullifyUser"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("leadId")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "LEADS"
    properties: NullifyTeamToLeadRelProperties = NullifyTeamToLeadRelProperties()


@dataclass(frozen=True)
class NullifyTeamSchema(CartographyNodeSchema):
    label: str = "NullifyTeam"
    properties: NullifyTeamNodeProperties = NullifyTeamNodeProperties()
    sub_resource_relationship: NullifyTeamToTenantRel = NullifyTeamToTenantRel()
    other_relationships: OtherRelationships = OtherRelationships(
        [
            NullifyTeamToRepositoryRel(),
            NullifyTeamToMemberRel(),
            NullifyTeamToLeadRel(),
        ],
    )

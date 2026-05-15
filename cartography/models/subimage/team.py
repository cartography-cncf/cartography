from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.nodes import ExtraNodeLabels
from cartography.models.core.relationships import CartographyRelProperties
from cartography.models.core.relationships import CartographyRelSchema
from cartography.models.core.relationships import LinkDirection
from cartography.models.core.relationships import make_target_node_matcher
from cartography.models.core.relationships import TargetNodeMatcher


@dataclass(frozen=True)
class SubImageTeamMemberNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id")
    email: PropertyRef = PropertyRef("email", extra_index=True)
    first_name: PropertyRef = PropertyRef("first_name")
    last_name: PropertyRef = PropertyRef("last_name")
    role: PropertyRef = PropertyRef("role")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class SubImageTeamMemberToTenantRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:SubImageTenant)-[:RESOURCE]->(:SubImageTeamMember)
class SubImageTeamMemberToTenantRel(CartographyRelSchema):
    target_node_label: str = "SubImageTenant"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("TENANT_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: SubImageTeamMemberToTenantRelProperties = (
        SubImageTeamMemberToTenantRelProperties()
    )


@dataclass(frozen=True)
class SubImageTeamMemberSchema(CartographyNodeSchema):
    label: str = "SubImageTeamMember"
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(["UserAccount"])
    properties: SubImageTeamMemberNodeProperties = SubImageTeamMemberNodeProperties()
    sub_resource_relationship: SubImageTeamMemberToTenantRel = (
        SubImageTeamMemberToTenantRel()
    )

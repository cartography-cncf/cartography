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
from cartography.models.ontology.labels import USER_ACCOUNT


@dataclass(frozen=True)
class SupabaseOrganizationMemberNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("user_id")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    email: PropertyRef = PropertyRef("email", extra_index=True)
    user_name: PropertyRef = PropertyRef("user_name")
    role_name: PropertyRef = PropertyRef("role_name")
    mfa_enabled: PropertyRef = PropertyRef("mfa_enabled")


@dataclass(frozen=True)
class SupabaseOrganizationMemberToOrganizationRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:SupabaseOrganization)-[:RESOURCE]->(:SupabaseOrganizationMember)
class SupabaseOrganizationMemberToOrganizationRel(CartographyRelSchema):
    target_node_label: str = "SupabaseOrganization"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("ORG_SLUG", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: SupabaseOrganizationMemberToOrganizationRelProperties = (
        SupabaseOrganizationMemberToOrganizationRelProperties()
    )


@dataclass(frozen=True)
class SupabaseOrganizationMemberSchema(CartographyNodeSchema):
    label: str = "SupabaseOrganizationMember"
    properties: SupabaseOrganizationMemberNodeProperties = (
        SupabaseOrganizationMemberNodeProperties()
    )
    sub_resource_relationship: SupabaseOrganizationMemberToOrganizationRel = (
        SupabaseOrganizationMemberToOrganizationRel()
    )
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels([USER_ACCOUNT])

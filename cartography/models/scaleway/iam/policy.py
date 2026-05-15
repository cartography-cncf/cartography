from dataclasses import dataclass
from typing import Optional

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
class ScalewayPolicyNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id")
    name: PropertyRef = PropertyRef("name")
    description: PropertyRef = PropertyRef("description")
    created_at: PropertyRef = PropertyRef("created_at")
    updated_at: PropertyRef = PropertyRef("updated_at")
    editable: PropertyRef = PropertyRef("editable")
    deletable: PropertyRef = PropertyRef("deletable")
    managed: PropertyRef = PropertyRef("managed")
    tags: PropertyRef = PropertyRef("tags")
    nb_rules: PropertyRef = PropertyRef("nb_rules")
    nb_scopes: PropertyRef = PropertyRef("nb_scopes")
    nb_permission_sets: PropertyRef = PropertyRef("nb_permission_sets")
    no_principal: PropertyRef = PropertyRef("no_principal")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class ScalewayPolicyToOrganizationRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:ScalewayOrganization)-[:RESOURCE]->(:ScalewayPolicy)
class ScalewayPolicyToOrganizationRel(CartographyRelSchema):
    target_node_label: str = "ScalewayOrganization"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("ORG_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: ScalewayPolicyToOrganizationRelProperties = (
        ScalewayPolicyToOrganizationRelProperties()
    )


@dataclass(frozen=True)
class ScalewayPolicyToUserRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:ScalewayPolicy)-[:APPLIES_TO]->(:ScalewayUser)
class ScalewayPolicyToUserRel(CartographyRelSchema):
    target_node_label: str = "ScalewayUser"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("user_id")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "APPLIES_TO"
    properties: ScalewayPolicyToUserRelProperties = ScalewayPolicyToUserRelProperties()


@dataclass(frozen=True)
class ScalewayPolicyToGroupRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:ScalewayPolicy)-[:APPLIES_TO]->(:ScalewayGroup)
class ScalewayPolicyToGroupRel(CartographyRelSchema):
    target_node_label: str = "ScalewayGroup"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("group_id")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "APPLIES_TO"
    properties: ScalewayPolicyToGroupRelProperties = (
        ScalewayPolicyToGroupRelProperties()
    )


@dataclass(frozen=True)
class ScalewayPolicyToApplicationRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:ScalewayPolicy)-[:APPLIES_TO]->(:ScalewayApplication)
class ScalewayPolicyToApplicationRel(CartographyRelSchema):
    target_node_label: str = "ScalewayApplication"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("application_id")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "APPLIES_TO"
    properties: ScalewayPolicyToApplicationRelProperties = (
        ScalewayPolicyToApplicationRelProperties()
    )


@dataclass(frozen=True)
class ScalewayPolicySchema(CartographyNodeSchema):
    label: str = "ScalewayPolicy"
    properties: ScalewayPolicyNodeProperties = ScalewayPolicyNodeProperties()
    sub_resource_relationship: ScalewayPolicyToOrganizationRel = (
        ScalewayPolicyToOrganizationRel()
    )
    other_relationships: Optional[OtherRelationships] = OtherRelationships(
        [
            ScalewayPolicyToUserRel(),
            ScalewayPolicyToGroupRel(),
            ScalewayPolicyToApplicationRel(),
        ]
    )

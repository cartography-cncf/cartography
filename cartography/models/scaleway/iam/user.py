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
class ScalewayUserNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id")
    email: PropertyRef = PropertyRef("email", extra_index=True)
    username: PropertyRef = PropertyRef("username")
    first_name: PropertyRef = PropertyRef("first_name")
    last_name: PropertyRef = PropertyRef("last_name")
    phone_number: PropertyRef = PropertyRef("phone_number")
    locale: PropertyRef = PropertyRef("locale")
    created_at: PropertyRef = PropertyRef("created_at")
    updated_at: PropertyRef = PropertyRef("updated_at")
    deletable: PropertyRef = PropertyRef("deletable")
    last_login_at: PropertyRef = PropertyRef("last_login_at")
    type: PropertyRef = PropertyRef("type")
    status: PropertyRef = PropertyRef("status")
    mfa: PropertyRef = PropertyRef("mfa")
    account_root_user_id: PropertyRef = PropertyRef("account_root_user_id")
    tags: PropertyRef = PropertyRef("tags")
    locked: PropertyRef = PropertyRef("locked")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class ScalewayUserToOrganizationRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:ScalewayOrganization)-[:RESOURCE]->(:ScalewayUser)
class ScalewayUserToOrganizationRel(CartographyRelSchema):
    target_node_label: str = "ScalewayOrganization"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("ORG_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: ScalewayUserToOrganizationRelProperties = (
        ScalewayUserToOrganizationRelProperties()
    )


@dataclass(frozen=True)
class ScalewayUserSchema(CartographyNodeSchema):
    label: str = "ScalewayUser"
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(
        ["UserAccount"]
    )  # UserAccount label is used for ontology mapping
    properties: ScalewayUserNodeProperties = ScalewayUserNodeProperties()
    sub_resource_relationship: ScalewayUserToOrganizationRel = (
        ScalewayUserToOrganizationRel()
    )

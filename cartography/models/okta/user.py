from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.relationships import CartographyRelProperties
from cartography.models.core.relationships import CartographyRelSchema
from cartography.models.core.relationships import LinkDirection
from cartography.models.core.relationships import make_target_node_matcher
from cartography.models.core.relationships import TargetNodeMatcher


@dataclass(frozen=True)
class OktaUserProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    first_name: PropertyRef = PropertyRef("first_name")
    last_name: PropertyRef = PropertyRef("last_name")
    login: PropertyRef = PropertyRef("login")
    email: PropertyRef = PropertyRef("email", extra_index=True)
    second_email: PropertyRef = PropertyRef("second_email")
    created: PropertyRef = PropertyRef("created")
    activated: PropertyRef = PropertyRef("activated")
    status_changed: PropertyRef = PropertyRef("status_changed")
    last_login: PropertyRef = PropertyRef("last_login")
    okta_last_updated: PropertyRef = PropertyRef("okta_last_updated")
    password_changed: PropertyRef = PropertyRef("password_changed")
    transition_to_status: PropertyRef = PropertyRef("transition_to_status")


@dataclass(frozen=True)
class OktaUserToOrganizationRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:OktaOrganization)-[:RESOURCE]->(:OktaUser)
class OktaUserToOrganizationRel(CartographyRelSchema):
    target_node_label: str = "OktaOrganization"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("ORG_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: OktaUserToOrganizationRelProperties = (
        OktaUserToOrganizationRelProperties()
    )


@dataclass(frozen=True)
class OktaUserSchema(CartographyNodeSchema):
    label: str = "OktaUser"
    properties: OktaUserProperties = OktaUserProperties()
    sub_resource_relationship: OktaUserToOrganizationRel = OktaUserToOrganizationRel()

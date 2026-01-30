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
class OktaAuthenticatorNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    created: PropertyRef = PropertyRef("created")
    key: PropertyRef = PropertyRef("key")
    last_updated: PropertyRef = PropertyRef("last_updated")
    name: PropertyRef = PropertyRef("name")
    # Provider properties (parsed from provider.configuration)
    provider_type: PropertyRef = PropertyRef("provider_type")
    provider_auth_port: PropertyRef = PropertyRef("provider_auth_port")
    provider_host_name: PropertyRef = PropertyRef("provider_host_name")
    provider_instance_id: PropertyRef = PropertyRef("provider_instance_id")
    provider_integration_key: PropertyRef = PropertyRef("provider_integration_key")
    provider_secret_key: PropertyRef = PropertyRef("provider_secret_key")
    provider_shared_secret: PropertyRef = PropertyRef("provider_shared_secret")
    provider_user_name_template: PropertyRef = PropertyRef(
        "provider_user_name_template"
    )
    provider_configuration: PropertyRef = PropertyRef("provider_configuration")
    # Settings properties (parsed from settings)
    settings_allowed_for: PropertyRef = PropertyRef("settings_allowed_for")
    settings_token_lifetime_minutes: PropertyRef = PropertyRef(
        "settings_token_lifetime_minutes"
    )
    settings_compliance: PropertyRef = PropertyRef("settings_compliance")
    settings_channel_binding: PropertyRef = PropertyRef("settings_channel_binding")
    settings_user_verification: PropertyRef = PropertyRef("settings_user_verification")
    settings_app_instance_id: PropertyRef = PropertyRef("settings_app_instance_id")
    settings: PropertyRef = PropertyRef("settings")
    status: PropertyRef = PropertyRef("status")
    authenticator_type: PropertyRef = PropertyRef("authenticator_type")


@dataclass(frozen=True)
class OktaAuthenticatorToOktaOrganizationRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:OktaAuthenticator)<-[:RESOURCE]-(:OktaOrganization)
class OktaAuthenticatorToOktaOrganizationRel(CartographyRelSchema):
    target_node_label: str = "OktaOrganization"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("OKTA_ORG_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: OktaAuthenticatorToOktaOrganizationRelProperties = (
        OktaAuthenticatorToOktaOrganizationRelProperties()
    )


@dataclass(frozen=True)
class OktaAuthenticatorSchema(CartographyNodeSchema):
    label: str = "OktaAuthenticator"
    properties: OktaAuthenticatorNodeProperties = OktaAuthenticatorNodeProperties()
    sub_resource_relationship: OktaAuthenticatorToOktaOrganizationRel = (
        OktaAuthenticatorToOktaOrganizationRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        rels=[],
    )

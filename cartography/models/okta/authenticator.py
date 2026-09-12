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
    id: PropertyRef = PropertyRef(
        "id", description="Unique identifier for the Okta resource."
    )
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last sync that observed this resource.",
    )
    created: PropertyRef = PropertyRef("created", description="Okta created.")
    key: PropertyRef = PropertyRef("key", description="Okta key.")
    last_updated: PropertyRef = PropertyRef(
        "last_updated", description="Okta last updated."
    )
    name: PropertyRef = PropertyRef("name", description="Okta name.")
    # Provider properties (parsed from provider.configuration)
    provider_type: PropertyRef = PropertyRef(
        "provider_type", description="Okta provider type."
    )
    provider_auth_port: PropertyRef = PropertyRef(
        "provider_auth_port", description="Okta provider auth port."
    )
    provider_host_name: PropertyRef = PropertyRef(
        "provider_host_name", description="Okta provider host name."
    )
    provider_instance_id: PropertyRef = PropertyRef(
        "provider_instance_id", description="Okta provider instance ID."
    )
    provider_integration_key: PropertyRef = PropertyRef(
        "provider_integration_key", description="Okta provider integration key."
    )
    provider_user_name_template: PropertyRef = PropertyRef(
        "provider_user_name_template", description="Okta provider user name template."
    )
    provider_configuration: PropertyRef = PropertyRef(
        "provider_configuration", description="Okta provider configuration."
    )
    # Settings properties (parsed from settings)
    settings_allowed_for: PropertyRef = PropertyRef(
        "settings_allowed_for", description="Okta settings allowed for."
    )
    settings_token_lifetime_minutes: PropertyRef = PropertyRef(
        "settings_token_lifetime_minutes",
        description="Okta settings token lifetime minutes.",
    )
    settings_compliance: PropertyRef = PropertyRef(
        "settings_compliance", description="Okta settings compliance."
    )
    settings_channel_binding: PropertyRef = PropertyRef(
        "settings_channel_binding", description="Okta settings channel binding."
    )
    settings_user_verification: PropertyRef = PropertyRef(
        "settings_user_verification", description="Okta settings user verification."
    )
    settings_app_instance_id: PropertyRef = PropertyRef(
        "settings_app_instance_id", description="Okta settings app instance ID."
    )
    settings: PropertyRef = PropertyRef("settings", description="Okta settings.")
    status: PropertyRef = PropertyRef("status", description="Okta status.")
    authenticator_type: PropertyRef = PropertyRef(
        "authenticator_type", description="Okta authenticator type."
    )


@dataclass(frozen=True)
class OktaAuthenticatorToOktaOrganizationRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last sync that observed this resource.",
    )


@dataclass(frozen=True)
# (:OktaAuthenticator)<-[:RESOURCE]-(:OktaOrganization)
class OktaAuthenticatorToOktaOrganizationRel(CartographyRelSchema):
    target_node_label: str = "OktaOrganization"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {
            "id": PropertyRef(
                "OKTA_ORG_ID",
                set_in_kwargs=True,
                description="Identifier of the owning Okta organization.",
            )
        },
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

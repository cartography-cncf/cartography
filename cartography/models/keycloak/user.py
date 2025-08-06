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
class KeycloakUserNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id")
    username: PropertyRef = PropertyRef("username")
    first_name: PropertyRef = PropertyRef("firstName")
    last_name: PropertyRef = PropertyRef("lastName")
    email: PropertyRef = PropertyRef("email")
    email_verified: PropertyRef = PropertyRef("emailVerified")
    self: PropertyRef = PropertyRef("self")  # WIP: Check if needed
    origin: PropertyRef = PropertyRef("origin")
    created_timestamp: PropertyRef = PropertyRef("createdTimestamp")
    enabled: PropertyRef = PropertyRef("enabled")
    totp: PropertyRef = PropertyRef("totp")
    federation_link: PropertyRef = PropertyRef("federationLink")  # WIP: Check if needed
    service_account_client_id: PropertyRef = PropertyRef("serviceAccountClientId")
    not_before: PropertyRef = PropertyRef("notBefore")
    # WIP: Check if we need that or a link to other entities
    user_profile_metadata_id: PropertyRef = PropertyRef("userProfileMetadata.id")
    credentials_id: PropertyRef = PropertyRef("credentials.id")
    federated_identities_id: PropertyRef = PropertyRef("federatedIdentities.id")
    client_consents_id: PropertyRef = PropertyRef("clientConsents.id")
    social_links_id: PropertyRef = PropertyRef("socialLinks.id")

    lastupdated: PropertyRef = PropertyRef("LASTUPDATED", set_in_kwargs=True)


@dataclass(frozen=True)
class KeycloakUserToRealmRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("LASTUPDATED", set_in_kwargs=True)


@dataclass(frozen=True)
# (:KeycloakUser)<-[:RESOURCE]-(:KeycloakRealm)
class KeycloakUserToRealmRel(CartographyRelSchema):
    target_node_label: str = "KeycloakRealm"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"name": PropertyRef("REALM", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: KeycloakUserToRealmRelProperties = KeycloakUserToRealmRelProperties()


@dataclass(frozen=True)
class KeycloakUserSchema(CartographyNodeSchema):
    label: str = "KeycloakUser"
    properties: KeycloakUserNodeProperties = KeycloakUserNodeProperties()
    sub_resource_relationship: KeycloakUserToRealmRel = KeycloakUserToRealmRel()

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
class KeycloakUserNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id", description="The unique identifier of the user")
    username: PropertyRef = PropertyRef(
        "username", description="The username for authentication"
    )
    first_name: PropertyRef = PropertyRef(
        "firstName", description="The first name of the user"
    )
    last_name: PropertyRef = PropertyRef(
        "lastName", description="The last name of the user"
    )
    email: PropertyRef = PropertyRef(
        "email", description="The email address of the user"
    )
    email_verified: PropertyRef = PropertyRef(
        "emailVerified", description="Whether the email address is verified"
    )
    origin: PropertyRef = PropertyRef(
        "origin", description="Origin of the user account"
    )
    created_timestamp: PropertyRef = PropertyRef(
        "createdTimestamp", description="Timestamp when the user was created"
    )
    enabled: PropertyRef = PropertyRef(
        "enabled", description="Whether the user account is enabled"
    )
    totp: PropertyRef = PropertyRef(
        "totp", description="Whether TOTP is enabled for the user"
    )
    service_account_client_id: PropertyRef = PropertyRef(
        "serviceAccountClientId", description="Client ID if this is a service account"
    )
    not_before: PropertyRef = PropertyRef(
        "notBefore", description="Not before timestamp for security"
    )
    lastupdated: PropertyRef = PropertyRef(
        "LASTUPDATED",
        set_in_kwargs=True,
        description="Timestamp of the last time the node was updated",
    )


@dataclass(frozen=True)
class KeycloakUserToRealmRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("LASTUPDATED", set_in_kwargs=True)


@dataclass(frozen=True)
# (:KeycloakUser)<-[:RESOURCE]-(:KeycloakRealm)
class KeycloakUserToRealmRel(CartographyRelSchema):
    """The realm contains the user."""

    target_node_label: str = "KeycloakRealm"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"name": PropertyRef("REALM", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: KeycloakUserToRealmRelProperties = KeycloakUserToRealmRelProperties()


@dataclass(frozen=True)
class KeycloakUserSchema(CartographyNodeSchema):
    """Represents a user in the Keycloak realm with authentication and profile information."""

    label: str = "KeycloakUser"
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(
        ["UserAccount"]
    )  # UserAccount label is used for ontology mapping
    properties: KeycloakUserNodeProperties = KeycloakUserNodeProperties()
    sub_resource_relationship: KeycloakUserToRealmRel = KeycloakUserToRealmRel()

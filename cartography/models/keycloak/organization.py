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
class KeycloakOrganizationNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "id", description="The unique identifier of the organization"
    )
    name: PropertyRef = PropertyRef("name", description="The name of the organization")
    alias: PropertyRef = PropertyRef(
        "alias", description="The alias of the organization"
    )
    enabled: PropertyRef = PropertyRef(
        "enabled", description="Whether the organization is enabled"
    )
    description: PropertyRef = PropertyRef(
        "description", description="The description of the organization"
    )
    redirect_url: PropertyRef = PropertyRef(
        "redirectUrl", description="The redirect URL for the organization"
    )
    lastupdated: PropertyRef = PropertyRef(
        "LASTUPDATED",
        set_in_kwargs=True,
        description="Timestamp of the last time the node was updated",
    )


@dataclass(frozen=True)
class KeycloakOrganizationToRealmRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("LASTUPDATED", set_in_kwargs=True)


@dataclass(frozen=True)
# (:KeycloakOrganization)<-[:RESOURCE]-(:KeycloakRealm)
class KeycloakOrganizationToRealmRel(CartographyRelSchema):
    """The realm contains the organization."""

    target_node_label: str = "KeycloakRealm"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"name": PropertyRef("REALM", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: KeycloakOrganizationToRealmRelProperties = (
        KeycloakOrganizationToRealmRelProperties()
    )


@dataclass(frozen=True)
class KeycloakOrganizationToManagedUserRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("LASTUPDATED", set_in_kwargs=True)


@dataclass(frozen=True)
# (:KeycloakOrganization)<-[:MANAGED_MEMBER_OF]-(:KeycloakUser)
class KeycloakOrganizationToManagedUserRel(CartographyRelSchema):
    """The user is a managed member of the organization."""

    target_node_label: str = "KeycloakUser"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("_managed_members", one_to_many=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "MANAGED_MEMBER_OF"
    properties: KeycloakOrganizationToManagedUserRelProperties = (
        KeycloakOrganizationToManagedUserRelProperties()
    )


@dataclass(frozen=True)
class KeycloakOrganizationToUnmanagedUserRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("LASTUPDATED", set_in_kwargs=True)


@dataclass(frozen=True)
# (:KeycloakOrganization)<-[:UNMANAGED_MEMBER_OF]-(:KeycloakUser)
class KeycloakOrganizationToUnmanagedUserRel(CartographyRelSchema):
    """The user is an unmanaged member of the organization."""

    target_node_label: str = "KeycloakUser"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("_unmanaged_members", one_to_many=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "UNMANAGED_MEMBER_OF"
    properties: KeycloakOrganizationToUnmanagedUserRelProperties = (
        KeycloakOrganizationToUnmanagedUserRelProperties()
    )


@dataclass(frozen=True)
class KeycloakOrganizationToIdentityProviderRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("LASTUPDATED", set_in_kwargs=True)


@dataclass(frozen=True)
# (:KeycloakOrganization)-[:ENFORCES]->(:KeycloakIdentityProvider)
class KeycloakOrganizationToIdentityProviderRel(CartographyRelSchema):
    """The organization enforces the identity provider."""

    target_node_label: str = "KeycloakIdentityProvider"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("_idp_ids", one_to_many=True)},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "ENFORCES"
    properties: KeycloakOrganizationToIdentityProviderRelProperties = (
        KeycloakOrganizationToIdentityProviderRelProperties()
    )


@dataclass(frozen=True)
class KeycloakOrganizationSchema(CartographyNodeSchema):
    """Represents a Keycloak organization, which is a logical grouping of users, domains, and identity providers within a realm. Organizations provide a way to isolate and manage different business entities or departments within the same Keycloak realm."""

    label: str = "KeycloakOrganization"
    properties: KeycloakOrganizationNodeProperties = (
        KeycloakOrganizationNodeProperties()
    )
    sub_resource_relationship: KeycloakOrganizationToRealmRel = (
        KeycloakOrganizationToRealmRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            KeycloakOrganizationToManagedUserRel(),
            KeycloakOrganizationToUnmanagedUserRel(),
            KeycloakOrganizationToIdentityProviderRel(),
        ]
    )

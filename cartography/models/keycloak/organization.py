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
    id: PropertyRef = PropertyRef("id")
    name: PropertyRef = PropertyRef("name")
    alias: PropertyRef = PropertyRef("alias")
    enabled: PropertyRef = PropertyRef("enabled")
    description: PropertyRef = PropertyRef("description")
    redirect_url: PropertyRef = PropertyRef("redirectUrl")
    lastupdated: PropertyRef = PropertyRef("LASTUPDATED", set_in_kwargs=True)


@dataclass(frozen=True)
class KeycloakOrganizationToRealmRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("LASTUPDATED", set_in_kwargs=True)


@dataclass(frozen=True)
# (:KeycloakOrganization)<-[:RESOURCE]-(:KeycloakRealm)
class KeycloakOrganizationToRealmRel(CartographyRelSchema):
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

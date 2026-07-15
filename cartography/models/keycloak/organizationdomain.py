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
class KeycloakOrganizationDomainNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "id", description="The unique identifier of the organization domain"
    )
    name: PropertyRef = PropertyRef(
        "name", extra_index=True, description="The domain name (indexed for queries)"
    )
    verified: PropertyRef = PropertyRef(
        "verified", description="Whether the domain has been verified"
    )
    lastupdated: PropertyRef = PropertyRef(
        "LASTUPDATED",
        set_in_kwargs=True,
        description="Timestamp of the last time the node was updated",
    )


@dataclass(frozen=True)
class KeycloakOrganizationDomainToRealmRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("LASTUPDATED", set_in_kwargs=True)


@dataclass(frozen=True)
# (:KeycloakOrganizationDomain)<-[:RESOURCE]-(:KeycloakRealm)
class KeycloakOrganizationDomainToRealmRel(CartographyRelSchema):
    """The realm contains the organization domain."""

    target_node_label: str = "KeycloakRealm"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"name": PropertyRef("REALM", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: KeycloakOrganizationDomainToRealmRelProperties = (
        KeycloakOrganizationDomainToRealmRelProperties()
    )


@dataclass(frozen=True)
class KeycloakOrganizationDomainToOrganizationRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("LASTUPDATED", set_in_kwargs=True)


@dataclass(frozen=True)
# (:KeycloakOrganizationDomain)-[:BELONGS_TO]->(:KeycloakOrganization)
class KeycloakOrganizationDomainToOrganizationRel(CartographyRelSchema):
    """The domain belongs to the organization."""

    target_node_label: str = "KeycloakOrganization"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("organization_id")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "BELONGS_TO"
    properties: KeycloakOrganizationDomainToOrganizationRelProperties = (
        KeycloakOrganizationDomainToOrganizationRelProperties()
    )


@dataclass(frozen=True)
class KeycloakOrganizationDomainSchema(CartographyNodeSchema):
    """Represents a domain that belongs to a Keycloak organization. Organization domains define which email domains are associated with an organization, and can be verified to ensure proper domain ownership."""

    label: str = "KeycloakOrganizationDomain"
    properties: KeycloakOrganizationDomainNodeProperties = (
        KeycloakOrganizationDomainNodeProperties()
    )
    sub_resource_relationship: KeycloakOrganizationDomainToRealmRel = (
        KeycloakOrganizationDomainToRealmRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            KeycloakOrganizationDomainToOrganizationRel(),
        ]
    )

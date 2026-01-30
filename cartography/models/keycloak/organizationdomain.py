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
    id: PropertyRef = PropertyRef("id")
    name: PropertyRef = PropertyRef("name", extra_index=True)
    verified: PropertyRef = PropertyRef("verified")
    lastupdated: PropertyRef = PropertyRef("LASTUPDATED", set_in_kwargs=True)


@dataclass(frozen=True)
class KeycloakOrganizationDomainToRealmRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("LASTUPDATED", set_in_kwargs=True)


@dataclass(frozen=True)
# (:KeycloakOrganizationDomain)<-[:RESOURCE]-(:KeycloakRealm)
class KeycloakOrganizationDomainToRealmRel(CartographyRelSchema):
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

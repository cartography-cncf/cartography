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
class ScalewayRegisteredDomainProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id")
    name: PropertyRef = PropertyRef("name")
    status: PropertyRef = PropertyRef("status")
    registrar: PropertyRef = PropertyRef("registrar")
    is_external: PropertyRef = PropertyRef("is_external")
    epp_code: PropertyRef = PropertyRef("epp_code")
    auto_renew_status: PropertyRef = PropertyRef("auto_renew_status")
    dnssec_status: PropertyRef = PropertyRef("dnssec_status")
    external_domain_registration_status: PropertyRef = PropertyRef(
        "external_domain_registration_status"
    )
    transfer_registration_status: PropertyRef = PropertyRef(
        "transfer_registration_status"
    )
    expired_at: PropertyRef = PropertyRef("expired_at")
    created_at: PropertyRef = PropertyRef("created_at")
    updated_at: PropertyRef = PropertyRef("updated_at")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class ScalewayRegisteredDomainToOrganizationRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:ScalewayOrganization)-[:RESOURCE]->(:ScalewayRegisteredDomain)
class ScalewayRegisteredDomainToOrganizationRel(CartographyRelSchema):
    target_node_label: str = "ScalewayOrganization"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("ORG_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: ScalewayRegisteredDomainToOrganizationRelProperties = (
        ScalewayRegisteredDomainToOrganizationRelProperties()
    )


@dataclass(frozen=True)
class ScalewayRegisteredDomainToProjectRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:ScalewayProject)-[:RESOURCE]->(:ScalewayRegisteredDomain)
class ScalewayRegisteredDomainToProjectRel(CartographyRelSchema):
    target_node_label: str = "ScalewayProject"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("project_id")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: ScalewayRegisteredDomainToProjectRelProperties = (
        ScalewayRegisteredDomainToProjectRelProperties()
    )


@dataclass(frozen=True)
class ScalewayRegisteredDomainSchema(CartographyNodeSchema):
    label: str = "ScalewayRegisteredDomain"
    properties: ScalewayRegisteredDomainProperties = (
        ScalewayRegisteredDomainProperties()
    )
    sub_resource_relationship: ScalewayRegisteredDomainToOrganizationRel = (
        ScalewayRegisteredDomainToOrganizationRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            ScalewayRegisteredDomainToProjectRel(),
        ]
    )

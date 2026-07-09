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
class ScalewayTemDomainProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id", extra_index=True)
    name: PropertyRef = PropertyRef("name", extra_index=True)
    organization_id: PropertyRef = PropertyRef("organization_id")
    project_id: PropertyRef = PropertyRef("project_id")
    status: PropertyRef = PropertyRef("status")
    region: PropertyRef = PropertyRef("region")
    last_error: PropertyRef = PropertyRef("last_error")
    created_at: PropertyRef = PropertyRef("created_at")
    revoked_at: PropertyRef = PropertyRef("revoked_at")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class ScalewayTemDomainToProjectRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:ScalewayProject)-[:RESOURCE]->(:ScalewayTemDomain)
class ScalewayTemDomainToProjectRel(CartographyRelSchema):
    target_node_label: str = "ScalewayProject"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("PROJECT_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: ScalewayTemDomainToProjectRelProperties = (
        ScalewayTemDomainToProjectRelProperties()
    )


@dataclass(frozen=True)
class ScalewayTemDomainSchema(CartographyNodeSchema):
    label: str = "ScalewayTemDomain"
    properties: ScalewayTemDomainProperties = ScalewayTemDomainProperties()
    sub_resource_relationship: ScalewayTemDomainToProjectRel = (
        ScalewayTemDomainToProjectRel()
    )

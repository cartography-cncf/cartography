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
class VercelProjectDomainNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    name: PropertyRef = PropertyRef("name", extra_index=True)
    redirect: PropertyRef = PropertyRef("redirect")
    redirect_status_code: PropertyRef = PropertyRef("redirectStatusCode")
    git_branch: PropertyRef = PropertyRef("gitBranch")
    verified: PropertyRef = PropertyRef("verified")
    created_at: PropertyRef = PropertyRef("createdAt")
    updated_at: PropertyRef = PropertyRef("updatedAt")


@dataclass(frozen=True)
class VercelProjectDomainToProjectRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:VercelProject)-[:RESOURCE]->(:VercelProjectDomain)
class VercelProjectDomainToProjectRel(CartographyRelSchema):
    target_node_label: str = "VercelProject"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("project_id", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: VercelProjectDomainToProjectRelProperties = (
        VercelProjectDomainToProjectRelProperties()
    )


@dataclass(frozen=True)
class VercelProjectDomainToDomainRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:VercelProjectDomain)-[:USES_DOMAIN]->(:VercelDomain)
class VercelProjectDomainToDomainRel(CartographyRelSchema):
    target_node_label: str = "VercelDomain"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("name")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "USES_DOMAIN"
    properties: VercelProjectDomainToDomainRelProperties = (
        VercelProjectDomainToDomainRelProperties()
    )


@dataclass(frozen=True)
class VercelProjectDomainSchema(CartographyNodeSchema):
    label: str = "VercelProjectDomain"
    properties: VercelProjectDomainNodeProperties = VercelProjectDomainNodeProperties()
    sub_resource_relationship: VercelProjectDomainToProjectRel = (
        VercelProjectDomainToProjectRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [VercelProjectDomainToDomainRel()],
    )

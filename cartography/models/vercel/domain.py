from dataclasses import dataclass
from typing import Optional

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.relationships import CartographyRelProperties
from cartography.models.core.relationships import CartographyRelSchema
from cartography.models.core.relationships import LinkDirection
from cartography.models.core.relationships import make_source_node_matcher
from cartography.models.core.relationships import make_target_node_matcher
from cartography.models.core.relationships import SourceNodeMatcher
from cartography.models.core.relationships import TargetNodeMatcher


@dataclass(frozen=True)
class VercelDomainNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("name")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    name: PropertyRef = PropertyRef("name", extra_index=True)
    service_type: PropertyRef = PropertyRef("serviceType")
    verified: PropertyRef = PropertyRef("verified")
    created_at: PropertyRef = PropertyRef("createdAt")
    expires_at: PropertyRef = PropertyRef("expiresAt")
    cdn_enabled: PropertyRef = PropertyRef("cdnEnabled")
    bought_at: PropertyRef = PropertyRef("boughtAt")


@dataclass(frozen=True)
class VercelDomainToTeamRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:VercelTeam)-[:RESOURCE]->(:VercelDomain)
class VercelDomainToTeamRel(CartographyRelSchema):
    target_node_label: str = "VercelTeam"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("TEAM_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: VercelDomainToTeamRelProperties = VercelDomainToTeamRelProperties()


@dataclass(frozen=True)
class VercelDomainSchema(CartographyNodeSchema):
    label: str = "VercelDomain"
    properties: VercelDomainNodeProperties = VercelDomainNodeProperties()
    sub_resource_relationship: VercelDomainToTeamRel = VercelDomainToTeamRel()


# Composite schema used when upserting VercelDomain nodes discovered via a
# project's domain endpoint. Only minimal properties are set so team-level
# fields (serviceType, verified, expiresAt, ...) are not clobbered when the
# same domain is also present in /v5/domains.
@dataclass(frozen=True)
class VercelDomainFromProjectProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("name")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    name: PropertyRef = PropertyRef("name", extra_index=True)


@dataclass(frozen=True)
class VercelDomainFromProjectSchema(CartographyNodeSchema):
    label: str = "VercelDomain"
    properties: VercelDomainFromProjectProperties = VercelDomainFromProjectProperties()
    sub_resource_relationship: Optional[CartographyRelSchema] = None


@dataclass(frozen=True)
class VercelProjectToDomainRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    _sub_resource_label: PropertyRef = PropertyRef(
        "_sub_resource_label", set_in_kwargs=True
    )
    _sub_resource_id: PropertyRef = PropertyRef("_sub_resource_id", set_in_kwargs=True)
    project_domain_id: PropertyRef = PropertyRef("project_domain_id")
    redirect: PropertyRef = PropertyRef("redirect")
    redirect_status_code: PropertyRef = PropertyRef("redirectStatusCode")
    git_branch: PropertyRef = PropertyRef("gitBranch")
    verified: PropertyRef = PropertyRef("verified")
    created_at: PropertyRef = PropertyRef("createdAt")
    updated_at: PropertyRef = PropertyRef("updatedAt")


@dataclass(frozen=True)
# (:VercelProject)-[:HAS_DOMAIN]->(:VercelDomain)
class VercelProjectToDomainRel(CartographyRelSchema):
    target_node_label: str = "VercelDomain"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("name")},
    )
    source_node_label: str = "VercelProject"
    source_node_matcher: SourceNodeMatcher = make_source_node_matcher(
        {"id": PropertyRef("project_id")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "HAS_DOMAIN"
    properties: VercelProjectToDomainRelProperties = (
        VercelProjectToDomainRelProperties()
    )

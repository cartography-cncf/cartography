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
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(["DNSZone"])
    sub_resource_relationship: VercelDomainToTeamRel = VercelDomainToTeamRel()

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
class ScalewayWebHostingProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id")
    status: PropertyRef = PropertyRef("status")
    offer_name: PropertyRef = PropertyRef("offer_name")
    region: PropertyRef = PropertyRef("region")
    domain: PropertyRef = PropertyRef("domain")
    dns_status: PropertyRef = PropertyRef("dns_status")
    domain_status: PropertyRef = PropertyRef("domain_status")
    protected: PropertyRef = PropertyRef("protected")
    created_at: PropertyRef = PropertyRef("created_at")
    updated_at: PropertyRef = PropertyRef("updated_at")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class ScalewayWebHostingToProjectRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:ScalewayProject)-[:RESOURCE]->(:ScalewayWebHosting)
class ScalewayWebHostingToProjectRel(CartographyRelSchema):
    target_node_label: str = "ScalewayProject"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("PROJECT_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: ScalewayWebHostingToProjectRelProperties = (
        ScalewayWebHostingToProjectRelProperties()
    )


@dataclass(frozen=True)
class ScalewayWebHostingSchema(CartographyNodeSchema):
    label: str = "ScalewayWebHosting"
    properties: ScalewayWebHostingProperties = ScalewayWebHostingProperties()
    sub_resource_relationship: ScalewayWebHostingToProjectRel = (
        ScalewayWebHostingToProjectRel()
    )

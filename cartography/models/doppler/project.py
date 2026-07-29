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
class DopplerProjectNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id")
    slug: PropertyRef = PropertyRef("slug")
    name: PropertyRef = PropertyRef("name")
    description: PropertyRef = PropertyRef("description")
    created_at: PropertyRef = PropertyRef("created_at")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class DopplerProjectToWorkplaceRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:DopplerWorkplace)-[:RESOURCE]->(:DopplerProject)
class DopplerProjectToWorkplaceRel(CartographyRelSchema):
    target_node_label: str = "DopplerWorkplace"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("WORKPLACE_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: DopplerProjectToWorkplaceRelProperties = (
        DopplerProjectToWorkplaceRelProperties()
    )


@dataclass(frozen=True)
class DopplerProjectSchema(CartographyNodeSchema):
    label: str = "DopplerProject"
    properties: DopplerProjectNodeProperties = DopplerProjectNodeProperties()
    sub_resource_relationship: DopplerProjectToWorkplaceRel = (
        DopplerProjectToWorkplaceRel()
    )

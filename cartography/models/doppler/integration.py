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
class DopplerIntegrationNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("slug")
    name: PropertyRef = PropertyRef("name")
    type: PropertyRef = PropertyRef("type")
    kind: PropertyRef = PropertyRef("kind")
    enabled: PropertyRef = PropertyRef("enabled")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class DopplerIntegrationToWorkplaceRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:DopplerWorkplace)-[:RESOURCE]->(:DopplerIntegration)
class DopplerIntegrationToWorkplaceRel(CartographyRelSchema):
    target_node_label: str = "DopplerWorkplace"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("WORKPLACE_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: DopplerIntegrationToWorkplaceRelProperties = (
        DopplerIntegrationToWorkplaceRelProperties()
    )


@dataclass(frozen=True)
class DopplerIntegrationSchema(CartographyNodeSchema):
    label: str = "DopplerIntegration"
    properties: DopplerIntegrationNodeProperties = DopplerIntegrationNodeProperties()
    sub_resource_relationship: DopplerIntegrationToWorkplaceRel = (
        DopplerIntegrationToWorkplaceRel()
    )

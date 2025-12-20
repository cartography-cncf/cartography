import logging
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

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class GCPBigtableInstanceProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("name")
    name: PropertyRef = PropertyRef("name")
    display_name: PropertyRef = PropertyRef("displayName")
    state: PropertyRef = PropertyRef("state")
    type: PropertyRef = PropertyRef("type")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class ProjectToBigtableInstanceRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class ProjectToBigtableInstanceRel(CartographyRelSchema):
    target_node_label: str = "GCPProject"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("PROJECT_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: ProjectToBigtableInstanceRelProperties = (
        ProjectToBigtableInstanceRelProperties()
    )


@dataclass(frozen=True)
class GCPBigtableInstanceSchema(CartographyNodeSchema):
    label: str = "GCPBigtableInstance"
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(["Database"])
    properties: GCPBigtableInstanceProperties = GCPBigtableInstanceProperties()
    sub_resource_relationship: ProjectToBigtableInstanceRel = (
        ProjectToBigtableInstanceRel()
    )

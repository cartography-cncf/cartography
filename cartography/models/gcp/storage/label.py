import logging
from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.relationships import CartographyRelProperties
from cartography.models.core.relationships import CartographyRelSchema
from cartography.models.core.relationships import LinkDirection
from cartography.models.core.relationships import make_target_node_matcher
from cartography.models.core.relationships import TargetNodeMatcher

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class GCPBucketLabelProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    key: PropertyRef = PropertyRef("key")
    value: PropertyRef = PropertyRef("value")


@dataclass(frozen=True)
class GCPBucketLabelToGCPProjectRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class GCPBucketLabelToGCPProjectRel(CartographyRelSchema):
    target_node_label: str = "GCPProject"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("project_number", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: GCPBucketLabelToGCPProjectRelProperties = (
        GCPBucketLabelToGCPProjectRelProperties()
    )


@dataclass(frozen=True)
class GCPBucketLabelSchema(CartographyNodeSchema):
    label: str = "GCPBucketLabel"
    properties: GCPBucketLabelProperties = GCPBucketLabelProperties()
    sub_resource_relationship: GCPBucketLabelToGCPProjectRel = (
        GCPBucketLabelToGCPProjectRel()
    )

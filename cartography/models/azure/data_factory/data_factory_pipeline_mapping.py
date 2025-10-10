import logging
from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.relationships import CartographyRelProperties
from cartography.models.core.relationships import CartographyRelSchema
from cartography.models.core.relationships import LinkDirection
from cartography.models.core.relationships import make_source_node_matcher
from cartography.models.core.relationships import make_target_node_matcher
from cartography.models.core.relationships import SourceNodeMatcher
from cartography.models.core.relationships import TargetNodeMatcher

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class PipelineUsesDatasetRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    _sub_resource_id: PropertyRef = PropertyRef("_sub_resource_id", set_in_kwargs=True)
    _sub_resource_label: PropertyRef = PropertyRef(
        "_sub_resource_label", set_in_kwargs=True
    )


@dataclass(frozen=True)
class PipelineUsesDatasetRel(CartographyRelSchema):
    source_node_label: str = "AzureDataFactoryPipeline"
    source_node_matcher: SourceNodeMatcher = make_source_node_matcher(
        {"id": PropertyRef("NODE_ID")},
    )
    target_node_label: str = "AzureDataFactoryDataset"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("DATASET_ID")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "USES_DATASET"
    properties: PipelineUsesDatasetRelProperties = PipelineUsesDatasetRelProperties()

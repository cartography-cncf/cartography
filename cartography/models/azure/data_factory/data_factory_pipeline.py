import logging
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

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class AzureDataFactoryPipelineProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id")
    name: PropertyRef = PropertyRef("name")
    description: PropertyRef = PropertyRef("description")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    factory_id: PropertyRef = PropertyRef("factory_id")
    subscription_id: PropertyRef = PropertyRef("subscription_id", set_in_kwargs=True)


@dataclass(frozen=True)
class AzureDataFactoryPipelineToFactoryRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AzureDataFactoryPipelineToFactoryRel(CartographyRelSchema):
    target_node_label: str = "AzureDataFactory"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("factory_id")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "CONTAINS"
    properties: AzureDataFactoryPipelineToFactoryRelProperties = (
        AzureDataFactoryPipelineToFactoryRelProperties()
    )


@dataclass(frozen=True)
class AzureDataFactoryPipelineToSubscriptionRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AzureDataFactoryPipelineToSubscriptionRel(CartographyRelSchema):
    target_node_label: str = "AzureSubscription"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("subscription_id", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: AzureDataFactoryPipelineToSubscriptionRelProperties = (
        AzureDataFactoryPipelineToSubscriptionRelProperties()
    )


@dataclass(frozen=True)
class PipelineUsesDatasetRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class PipelineUsesDatasetRel(CartographyRelSchema):
    target_node_label: str = "AzureDataFactoryDataset"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("dataset_id")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "USES_DATASET"
    properties: PipelineUsesDatasetRelProperties = PipelineUsesDatasetRelProperties()


@dataclass(frozen=True)
class AzureDataFactoryPipelineSchema(CartographyNodeSchema):
    label: str = "AzureDataFactoryPipeline"
    properties: AzureDataFactoryPipelineProperties = (
        AzureDataFactoryPipelineProperties()
    )
    sub_resource_relationship: AzureDataFactoryPipelineToSubscriptionRel = (
        AzureDataFactoryPipelineToSubscriptionRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            AzureDataFactoryPipelineToFactoryRel(),
            PipelineUsesDatasetRel(),
        ],
    )

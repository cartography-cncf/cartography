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
class AzureDataFactoryDatasetProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id")
    name: PropertyRef = PropertyRef("name")
    type: PropertyRef = PropertyRef("type")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AzureDataFactoryDatasetToFactoryRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AzureDataFactoryDatasetToFactoryRel(CartographyRelSchema):
    target_node_label: str = "AzureDataFactory"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("FACTORY_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "CONTAINS"
    properties: AzureDataFactoryDatasetToFactoryRelProperties = (
        AzureDataFactoryDatasetToFactoryRelProperties()
    )


@dataclass(frozen=True)
class AzureDataFactoryDatasetSchema(CartographyNodeSchema):
    label: str = "AzureDataFactoryDataset"
    properties: AzureDataFactoryDatasetProperties = AzureDataFactoryDatasetProperties()
    sub_resource_relationship: AzureDataFactoryDatasetToFactoryRel = (
        AzureDataFactoryDatasetToFactoryRel()
    )

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
class GCPBigQueryDatasetProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef('id', extra_index=True)
    lastupdated: PropertyRef = PropertyRef('lastupdated', set_in_kwargs=True)
    dataset_id: PropertyRef = PropertyRef('dataset_id')
    friendly_name: PropertyRef = PropertyRef('friendly_name')
    description: PropertyRef = PropertyRef('description')
    location: PropertyRef = PropertyRef('location')
    full_dataset_id: PropertyRef = PropertyRef('full_dataset_id')
    created: PropertyRef = PropertyRef('created')
    modified: PropertyRef = PropertyRef('modified')


@dataclass(frozen=True)
class GCPBigQueryDatasetToProjectRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef('lastupdated', set_in_kwargs=True)


@dataclass(frozen=True)
class GCPBigQueryDatasetToProjectRel(CartographyRelSchema):
    target_node_label: str = 'GCPProject'
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {'id': PropertyRef('PROJECT_ID', set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = 'RESOURCE'
    properties: GCPBigQueryDatasetToProjectRelProperties = GCPBigQueryDatasetToProjectRelProperties()


@dataclass(frozen=True)
class GCPBigQueryDatasetSchema(CartographyNodeSchema):
    label: str = 'GCPBigQueryDataset'
    properties: GCPBigQueryDatasetProperties = GCPBigQueryDatasetProperties()
    sub_resource_relationship: GCPBigQueryDatasetToProjectRel = GCPBigQueryDatasetToProjectRel()

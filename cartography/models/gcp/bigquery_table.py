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


@dataclass(frozen=True)
class GCPBigQueryTableProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef('id', extra_index=True)
    lastupdated: PropertyRef = PropertyRef('lastupdated', set_in_kwargs=True)
    table_id: PropertyRef = PropertyRef('table_id')
    type: PropertyRef = PropertyRef('type')
    creation_time: PropertyRef = PropertyRef('creation_time')
    expires: PropertyRef = PropertyRef('expires')


@dataclass(frozen=True)
class GCPBigQueryTableToDatasetRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef('lastupdated', set_in_kwargs=True)


@dataclass(frozen=True)
class GCPBigQueryTableToDatasetRel(CartographyRelSchema):
    target_node_label: str = 'GCPBigQueryDataset'
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {'id': PropertyRef('dataset_full_id')},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = 'CONTAINS'
    properties: GCPBigQueryTableToDatasetRelProperties = GCPBigQueryTableToDatasetRelProperties()


@dataclass(frozen=True)
class GCPBigQueryTableSchema(CartographyNodeSchema):
    label: str = 'GCPBigQueryTable'
    properties: GCPBigQueryTableProperties = GCPBigQueryTableProperties()
    other_relationships: OtherRelationships = OtherRelationships([GCPBigQueryTableToDatasetRel()])

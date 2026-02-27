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


@dataclass(frozen=True)
class GCPBigQueryDatasetProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    dataset_id: PropertyRef = PropertyRef("dataset_id")
    friendly_name: PropertyRef = PropertyRef("friendly_name")
    description: PropertyRef = PropertyRef("description")
    location: PropertyRef = PropertyRef("location")
    creation_time: PropertyRef = PropertyRef("creation_time")
    last_modified_time: PropertyRef = PropertyRef("last_modified_time")
    default_table_expiration_ms: PropertyRef = PropertyRef("default_table_expiration_ms")
    default_partition_expiration_ms: PropertyRef = PropertyRef("default_partition_expiration_ms")


@dataclass(frozen=True)
class ProjectToDatasetRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class ProjectToDatasetRel(CartographyRelSchema):
    target_node_label: str = "GCPProject"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("PROJECT_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: ProjectToDatasetRelProperties = ProjectToDatasetRelProperties()


@dataclass(frozen=True)
class GCPBigQueryDatasetSchema(CartographyNodeSchema):
    label: str = "GCPBigQueryDataset"
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(["Database"])
    properties: GCPBigQueryDatasetProperties = GCPBigQueryDatasetProperties()
    sub_resource_relationship: ProjectToDatasetRel = ProjectToDatasetRel()

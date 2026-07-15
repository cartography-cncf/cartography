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
    id: PropertyRef = PropertyRef(
        "id", description="Stable identifier for this resource."
    )
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last time the node was updated.",
    )
    dataset_id: PropertyRef = PropertyRef(
        "dataset_id", description="The short dataset ID."
    )
    friendly_name: PropertyRef = PropertyRef(
        "friendly_name", description="User-friendly name for the dataset."
    )
    description: PropertyRef = PropertyRef(
        "description", description="Description of the dataset."
    )
    location: PropertyRef = PropertyRef(
        "location", description="Geographic location of the dataset (e.g., US, EU)."
    )
    creation_time: PropertyRef = PropertyRef(
        "creation_time", description="Creation time of the dataset."
    )
    last_modified_time: PropertyRef = PropertyRef(
        "last_modified_time", description="Last modification time of the dataset."
    )
    default_table_expiration_ms: PropertyRef = PropertyRef(
        "default_table_expiration_ms",
        description="Default expiration time for tables in milliseconds.",
    )
    default_partition_expiration_ms: PropertyRef = PropertyRef(
        "default_partition_expiration_ms",
        description="Default expiration time for partitions in milliseconds.",
    )
    default_kms_key_name: PropertyRef = PropertyRef(
        "default_kms_key_name",
        description="Default customer-managed encryption key configured for new tables in the dataset, when present.",
    )
    access_entries: PropertyRef = PropertyRef(
        "access_entries",
        description="JSON string containing the dataset access entries returned by the BigQuery API.",
    )


@dataclass(frozen=True)
class ProjectToDatasetRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last sync that observed this data.",
    )


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
    """Represents a GCP BigQuery Dataset."""

    label: str = "GCPBigQueryDataset"
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(["Database"])
    properties: GCPBigQueryDatasetProperties = GCPBigQueryDatasetProperties()
    sub_resource_relationship: ProjectToDatasetRel = ProjectToDatasetRel()

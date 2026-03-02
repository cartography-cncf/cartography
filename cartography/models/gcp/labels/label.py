from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.nodes import ExtraNodeLabels


@dataclass(frozen=True)
class GCPLabelNodeProperties(CartographyNodeProperties):
    """
    Properties for GCPLabel nodes.

    Note: GCPLabel nodes are created via template queries in cartography/intel/gcp/labels.py
    because they have dynamic LABELED relationships to many different resource types.
    The id is computed as "{resource_id}:{key}:{value}" during ingestion.
    """

    id: PropertyRef = PropertyRef("id")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    key: PropertyRef = PropertyRef("key")
    value: PropertyRef = PropertyRef("value")
    resource_type: PropertyRef = PropertyRef("resource_type")


@dataclass(frozen=True)
class GCPLabelSchema(CartographyNodeSchema):
    """
    GCPLabel schema.

    Note: This schema is for documentation purposes. The actual node creation uses
    template-based queries because GCPLabel has dynamic LABELED relationships to many
    different resource types (GCPInstance, GCPBucket, GKECluster, etc.). The cleanup is also
    handled manually due to this dynamic nature.

    The LABELED relationship goes FROM the resource TO the GCPLabel:
    (resource)-[:LABELED]->(GCPLabel)
    """

    label: str = "GCPLabel"
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(["Label"])
    properties: GCPLabelNodeProperties = GCPLabelNodeProperties()
    sub_resource_relationship: None = None

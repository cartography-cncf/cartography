from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.nodes import ExtraNodeLabels


@dataclass(frozen=True)
class AWSTagNodeProperties(CartographyNodeProperties):
    """
    Properties for AWSTag nodes.

    Note: AWSTag nodes are created via template queries in resourcegroupstaggingapi.py
    because they have dynamic TAGGED relationships to many different resource types.
    The id is computed as "Key:Value" during ingestion.
    """

    id: PropertyRef = PropertyRef("id")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    key: PropertyRef = PropertyRef("key")
    value: PropertyRef = PropertyRef("value")
    region: PropertyRef = PropertyRef("region", set_in_kwargs=True)


@dataclass(frozen=True)
class AWSTagSchema(CartographyNodeSchema):
    """
    AWSTag schema.

    Note: This schema is for documentation purposes. The actual node creation uses
    template-based queries because AWSTag has dynamic TAGGED relationships to many
    different resource types (EC2Instance, S3Bucket, etc.). The cleanup is also
    handled manually due to this dynamic nature.

    The TAGGED relationship goes FROM the resource TO the AWSTag:
    (resource)-[:TAGGED]->(AWSTag)
    """

    label: str = "AWSTag"
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(["Tag"])
    properties: AWSTagNodeProperties = AWSTagNodeProperties()
    sub_resource_relationship: None = None

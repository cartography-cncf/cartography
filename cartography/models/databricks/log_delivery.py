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
class DatabricksLogDeliveryNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id")
    config_id: PropertyRef = PropertyRef("config_id", extra_index=True)
    config_name: PropertyRef = PropertyRef("config_name", extra_index=True)
    log_type: PropertyRef = PropertyRef("log_type")
    output_format: PropertyRef = PropertyRef("output_format")
    status: PropertyRef = PropertyRef("status")
    s3_bucket_name: PropertyRef = PropertyRef("s3_bucket_name", extra_index=True)
    delivery_path_prefix: PropertyRef = PropertyRef("delivery_path_prefix")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class DatabricksLogDeliveryToAccountRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:DatabricksAccount)-[:RESOURCE]->(:DatabricksLogDelivery)
class DatabricksLogDeliveryToAccountRel(CartographyRelSchema):
    target_node_label: str = "DatabricksAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("ACCOUNT_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: DatabricksLogDeliveryToAccountRelProperties = (
        DatabricksLogDeliveryToAccountRelProperties()
    )


@dataclass(frozen=True)
class DatabricksLogDeliveryToS3RelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:DatabricksLogDelivery)-[:DELIVERS_TO]->(:S3Bucket)
class DatabricksLogDeliveryToS3Rel(CartographyRelSchema):
    target_node_label: str = "S3Bucket"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"name": PropertyRef("s3_bucket_name")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "DELIVERS_TO"
    properties: DatabricksLogDeliveryToS3RelProperties = (
        DatabricksLogDeliveryToS3RelProperties()
    )


@dataclass(frozen=True)
class DatabricksLogDeliverySchema(CartographyNodeSchema):
    label: str = "DatabricksLogDelivery"
    properties: DatabricksLogDeliveryNodeProperties = (
        DatabricksLogDeliveryNodeProperties()
    )
    sub_resource_relationship: DatabricksLogDeliveryToAccountRel = (
        DatabricksLogDeliveryToAccountRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [DatabricksLogDeliveryToS3Rel()],
    )

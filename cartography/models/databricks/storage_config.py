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
class DatabricksStorageConfigNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id")
    storage_configuration_id: PropertyRef = PropertyRef(
        "storage_configuration_id", extra_index=True
    )
    storage_configuration_name: PropertyRef = PropertyRef(
        "storage_configuration_name", extra_index=True
    )
    root_bucket_name: PropertyRef = PropertyRef("root_bucket_name", extra_index=True)
    created_time: PropertyRef = PropertyRef("created_time")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class DatabricksStorageConfigToAccountRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:DatabricksAccount)-[:RESOURCE]->(:DatabricksStorageConfig)
class DatabricksStorageConfigToAccountRel(CartographyRelSchema):
    target_node_label: str = "DatabricksAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("ACCOUNT_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: DatabricksStorageConfigToAccountRelProperties = (
        DatabricksStorageConfigToAccountRelProperties()
    )


@dataclass(frozen=True)
class DatabricksStorageConfigToS3RelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:DatabricksStorageConfig)-[:BACKED_BY]->(:S3Bucket)
class DatabricksStorageConfigToS3Rel(CartographyRelSchema):
    target_node_label: str = "S3Bucket"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"name": PropertyRef("root_bucket_name")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "BACKED_BY"
    properties: DatabricksStorageConfigToS3RelProperties = (
        DatabricksStorageConfigToS3RelProperties()
    )


@dataclass(frozen=True)
class DatabricksStorageConfigSchema(CartographyNodeSchema):
    label: str = "DatabricksStorageConfig"
    properties: DatabricksStorageConfigNodeProperties = (
        DatabricksStorageConfigNodeProperties()
    )
    sub_resource_relationship: DatabricksStorageConfigToAccountRel = (
        DatabricksStorageConfigToAccountRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [DatabricksStorageConfigToS3Rel()],
    )

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
class AzureStorageFileShareProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    type: PropertyRef = PropertyRef("type")
    name: PropertyRef = PropertyRef("name")
    lastmodifiedtime: PropertyRef = PropertyRef("last_modified_time")
    sharequota: PropertyRef = PropertyRef("share_quota")
    accesstier: PropertyRef = PropertyRef("access_tier")
    deleted: PropertyRef = PropertyRef("deleted")
    accesstierchangetime: PropertyRef = PropertyRef("access_tier_change_time")
    accesstierstatus: PropertyRef = PropertyRef("access_tier_status")
    deletedtime: PropertyRef = PropertyRef("deleted_time")
    enabledprotocols: PropertyRef = PropertyRef("enabled_protocols")
    remainingretentiondays: PropertyRef = PropertyRef("remaining_retention_days")
    shareusagebytes: PropertyRef = PropertyRef("share_usage_bytes")
    version: PropertyRef = PropertyRef("version")


@dataclass(frozen=True)
class AzureStorageFileShareToStorageFileServiceProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:AzureStorageFileService)-[:CONTAINS]->(:AzureStorageFileShare)
class AzureStorageFileShareToStorageFileServiceRel(CartographyRelSchema):
    target_node_label: str = "AzureStorageFileService"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("service_id")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "CONTAINS"
    properties: AzureStorageFileShareToStorageFileServiceProperties = (
        AzureStorageFileShareToStorageFileServiceProperties()
    )


@dataclass(frozen=True)
class AzureStorageFileShareToSubscriptionRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:AzureSubscription)-[:RESOURCE]->(:AzureStorageFileShare)
class AzureStorageFileShareToSubscriptionRel(CartographyRelSchema):
    target_node_label: str = "AzureSubscription"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("AZURE_SUBSCRIPTION_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: AzureStorageFileShareToSubscriptionRelProperties = (
        AzureStorageFileShareToSubscriptionRelProperties()
    )


@dataclass(frozen=True)
class AzureStorageFileShareSchema(CartographyNodeSchema):
    label: str = "AzureStorageFileShare"
    properties: AzureStorageFileShareProperties = AzureStorageFileShareProperties()
    sub_resource_relationship: AzureStorageFileShareToSubscriptionRel = (
        AzureStorageFileShareToSubscriptionRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            AzureStorageFileShareToStorageFileServiceRel(),
        ]
    )

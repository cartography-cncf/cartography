from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.nodes import ExtraNodeLabels
from cartography.models.core.relationships import CartographyRelProperties
from cartography.models.core.relationships import CartographyRelSchema
from cartography.models.core.relationships import LinkDirection
from cartography.models.core.relationships import make_target_node_matcher
from cartography.models.core.relationships import OtherRelationships
from cartography.models.core.relationships import TargetNodeMatcher
from cartography.models.ontology.labels import FILE_STORAGE


@dataclass(frozen=True)
class AzureStorageFileShareProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id", description="Azure resource ID.")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    type: PropertyRef = PropertyRef("type", description="Azure resource type.")
    name: PropertyRef = PropertyRef("name", description="Azure resource name.")
    lastmodifiedtime: PropertyRef = PropertyRef(
        "last_modified_time", description="Time when the file share was last modified."
    )
    sharequota: PropertyRef = PropertyRef(
        "share_quota", description="Provisioned size of the file share, in gibibytes."
    )
    accesstier: PropertyRef = PropertyRef(
        "access_tier", description="Access tier of the file share."
    )
    deleted: PropertyRef = PropertyRef(
        "deleted", description="Whether the file share is soft deleted."
    )
    accesstierchangetime: PropertyRef = PropertyRef(
        "access_tier_change_time",
        description="Time when the file share access tier last changed.",
    )
    accesstierstatus: PropertyRef = PropertyRef(
        "access_tier_status", description="Status of the file share access tier change."
    )
    deletedtime: PropertyRef = PropertyRef(
        "deleted_time", description="Time when the file share was deleted."
    )
    enabledprotocols: PropertyRef = PropertyRef(
        "enabled_protocols", description="Protocol enabled for the file share."
    )
    remainingretentiondays: PropertyRef = PropertyRef(
        "remaining_retention_days",
        description="Remaining retention period for the soft-deleted file share, in days.",
    )
    shareusagebytes: PropertyRef = PropertyRef(
        "share_usage_bytes",
        description="Approximate size of data stored in the file share, in bytes.",
    )
    version: PropertyRef = PropertyRef(
        "version", description="Version of the soft-deleted file share."
    )


@dataclass(frozen=True)
class AzureStorageFileShareToStorageFileServiceRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:AzureStorageFileService)-[:CONTAINS]->(:AzureStorageFileShare)
class AzureStorageFileShareToStorageFileServiceRel(CartographyRelSchema):
    """An Azure Files service contains the file share."""

    target_node_label: str = "AzureStorageFileService"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("service_id")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "CONTAINS"
    properties: AzureStorageFileShareToStorageFileServiceRelProperties = (
        AzureStorageFileShareToStorageFileServiceRelProperties()
    )


@dataclass(frozen=True)
class AzureStorageFileShareToSubscriptionRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:AzureSubscription)-[:RESOURCE]->(:AzureStorageFileShare)
class AzureStorageFileShareToSubscriptionRel(CartographyRelSchema):
    """An Azure subscription contains the file share as a resource."""

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
    """An Azure file share hosted by an Azure Files service."""

    label: str = "AzureStorageFileShare"
    properties: AzureStorageFileShareProperties = AzureStorageFileShareProperties()
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels([FILE_STORAGE])
    sub_resource_relationship: AzureStorageFileShareToSubscriptionRel = (
        AzureStorageFileShareToSubscriptionRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            AzureStorageFileShareToStorageFileServiceRel(),
        ]
    )

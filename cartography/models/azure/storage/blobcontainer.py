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
from cartography.models.ontology.labels import OBJECT_STORAGE


@dataclass(frozen=True)
class AzureStorageBlobContainerProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id", description="Azure resource ID.")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    type: PropertyRef = PropertyRef("type", description="Azure resource type.")
    name: PropertyRef = PropertyRef("name", description="Azure resource name.")
    deleted: PropertyRef = PropertyRef(
        "deleted", description="Whether the blob container is soft deleted."
    )
    deletedtime: PropertyRef = PropertyRef(
        "deleted_time", description="Time when the blob container was deleted."
    )
    default_encryption_scope: PropertyRef = PropertyRef(
        "default_encryption_scope",
        description="Default encryption scope used for writes to the blob container.",
    )
    public_access: PropertyRef = PropertyRef(
        "public_access",
        description="Level of anonymous public access allowed for the blob container.",
    )
    lease_status: PropertyRef = PropertyRef(
        "lease_status", description="Lease status of the blob container."
    )
    lease_state: PropertyRef = PropertyRef(
        "lease_state", description="Lease state of the blob container."
    )
    last_modified_time: PropertyRef = PropertyRef(
        "last_modified_time",
        description="Time when the blob container was last modified.",
    )
    remaining_retention_days: PropertyRef = PropertyRef(
        "remaining_retention_days",
        description="Remaining retention period for the soft-deleted blob container, in days.",
    )
    version: PropertyRef = PropertyRef(
        "version", description="Version of the soft-deleted blob container."
    )
    has_immutability_policy: PropertyRef = PropertyRef(
        "has_immutability_policy",
        description="Whether the blob container has an immutability policy.",
    )
    has_legal_hold: PropertyRef = PropertyRef(
        "has_legal_hold",
        description="Whether the blob container has at least one legal hold tag.",
    )
    lease_duration: PropertyRef = PropertyRef(
        "leaseDuration", description="Lease duration of the blob container."
    )


@dataclass(frozen=True)
class AzureStorageBlobContainerToStorageBlobServiceRelProperties(
    CartographyRelProperties
):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:AzureStorageBlobService)-[:CONTAINS]->(:AzureStorageBlobContainer)
class AzureStorageBlobContainerToStorageBlobServiceRel(CartographyRelSchema):
    """An Azure Blob Storage service contains the blob container."""

    target_node_label: str = "AzureStorageBlobService"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("service_id")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "CONTAINS"
    properties: AzureStorageBlobContainerToStorageBlobServiceRelProperties = (
        AzureStorageBlobContainerToStorageBlobServiceRelProperties()
    )


@dataclass(frozen=True)
class AzureStorageBlobContainerToSubscriptionRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:AzureSubscription)-[:RESOURCE]->(:AzureStorageBlobContainer)
class AzureStorageBlobContainerToSubscriptionRel(CartographyRelSchema):
    """An Azure subscription contains the blob container as a resource."""

    target_node_label: str = "AzureSubscription"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("AZURE_SUBSCRIPTION_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: AzureStorageBlobContainerToSubscriptionRelProperties = (
        AzureStorageBlobContainerToSubscriptionRelProperties()
    )


@dataclass(frozen=True)
class AzureStorageBlobContainerSchema(CartographyNodeSchema):
    """An Azure Blob Storage container that organizes blobs within a blob service."""

    label: str = "AzureStorageBlobContainer"
    properties: AzureStorageBlobContainerProperties = (
        AzureStorageBlobContainerProperties()
    )
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels([OBJECT_STORAGE])
    sub_resource_relationship: AzureStorageBlobContainerToSubscriptionRel = (
        AzureStorageBlobContainerToSubscriptionRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            AzureStorageBlobContainerToStorageBlobServiceRel(),
        ]
    )

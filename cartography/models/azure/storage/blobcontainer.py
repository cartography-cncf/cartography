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
class AzureStorageBlobContainerProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    type: PropertyRef = PropertyRef("type")
    name: PropertyRef = PropertyRef("name")
    deleted: PropertyRef = PropertyRef("deleted")
    deletedtime: PropertyRef = PropertyRef("deleted_time")
    default_encryption_scope: PropertyRef = PropertyRef("default_encryption_scope")
    public_access: PropertyRef = PropertyRef("public_access")
    lease_status: PropertyRef = PropertyRef("lease_status")
    lease_state: PropertyRef = PropertyRef("lease_state")
    last_modified_time: PropertyRef = PropertyRef("last_modified_time")
    remaining_retention_days: PropertyRef = PropertyRef("remaining_retention_days")
    version: PropertyRef = PropertyRef("version")
    has_immutability_policy: PropertyRef = PropertyRef("has_immutability_policy")
    has_legal_hold: PropertyRef = PropertyRef("has_legal_hold")
    lease_duration: PropertyRef = PropertyRef("leaseDuration")


@dataclass(frozen=True)
class AzureStorageBlobContainerToStorageBlobServiceProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:AzureStorageBlobService)-[:CONTAINS]->(:AzureStorageBlobContainer)
class AzureStorageBlobContainerToStorageBlobServiceRel(CartographyRelSchema):
    target_node_label: str = "AzureStorageBlobService"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("service_id")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "CONTAINS"
    properties: AzureStorageBlobContainerToStorageBlobServiceProperties = (
        AzureStorageBlobContainerToStorageBlobServiceProperties()
    )


@dataclass(frozen=True)
class AzureStorageBlobContainerToSubscriptionRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:AzureSubscription)-[:RESOURCE]->(:AzureStorageBlobContainer)
class AzureStorageBlobContainerToSubscriptionRel(CartographyRelSchema):
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
    label: str = "AzureStorageBlobContainer"
    properties: AzureStorageBlobContainerProperties = (
        AzureStorageBlobContainerProperties()
    )
    sub_resource_relationship: AzureStorageBlobContainerToSubscriptionRel = (
        AzureStorageBlobContainerToSubscriptionRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            AzureStorageBlobContainerToStorageBlobServiceRel(),
        ]
    )

import logging
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

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class AzureDataLakeFileSystemProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "id", description="Full Azure resource ID of the file system."
    )
    name: PropertyRef = PropertyRef("name", description="Name of the file system.")
    public_access: PropertyRef = PropertyRef(
        "public_access",
        description="Configured anonymous public access level for the file system.",
    )
    last_modified_time: PropertyRef = PropertyRef(
        "last_modified_time",
        description="Timestamp when the file system was last modified.",
    )
    has_immutability_policy: PropertyRef = PropertyRef(
        "has_immutability_policy",
        description="Whether the file system has an immutability policy.",
    )
    has_legal_hold: PropertyRef = PropertyRef(
        "has_legal_hold", description="Whether the file system has a legal hold."
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AzureDataLakeFileSystemToStorageAccountRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:AzureStorageAccount)-[:CONTAINS]->(:AzureDataLakeFileSystem)
class AzureDataLakeFileSystemToStorageAccountRel(CartographyRelSchema):
    """An Azure storage account contains the Data Lake file system."""

    target_node_label: str = "AzureStorageAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("STORAGE_ACCOUNT_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "CONTAINS"
    properties: AzureDataLakeFileSystemToStorageAccountRelProperties = (
        AzureDataLakeFileSystemToStorageAccountRelProperties()
    )


@dataclass(frozen=True)
class AzureDataLakeFileSystemToSubscriptionRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:AzureSubscription)-[:RESOURCE]->(:AzureDataLakeFileSystem)
class AzureDataLakeFileSystemToSubscriptionRel(CartographyRelSchema):
    """An Azure subscription contains the Data Lake file system as a resource."""

    target_node_label: str = "AzureSubscription"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("AZURE_SUBSCRIPTION_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: AzureDataLakeFileSystemToSubscriptionRelProperties = (
        AzureDataLakeFileSystemToSubscriptionRelProperties()
    )


@dataclass(frozen=True)
class AzureDataLakeFileSystemSchema(CartographyNodeSchema):
    """A hierarchical file system in an Azure Data Lake Storage account."""

    label: str = "AzureDataLakeFileSystem"
    properties: AzureDataLakeFileSystemProperties = AzureDataLakeFileSystemProperties()
    sub_resource_relationship: AzureDataLakeFileSystemToSubscriptionRel = (
        AzureDataLakeFileSystemToSubscriptionRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        rels=[AzureDataLakeFileSystemToStorageAccountRel()],
    )

import logging
from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.relationships import CartographyRelProperties
from cartography.models.core.relationships import CartographyRelSchema
from cartography.models.core.relationships import LinkDirection
from cartography.models.core.relationships import make_target_node_matcher
from cartography.models.core.relationships import TargetNodeMatcher

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class AzureDataLakeFileSystemProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id")
    name: PropertyRef = PropertyRef("name")
    public_access: PropertyRef = PropertyRef("public_access")
    last_modified_time: PropertyRef = PropertyRef("last_modified_time")
    has_immutability_policy: PropertyRef = PropertyRef("has_immutability_policy")
    has_legal_hold: PropertyRef = PropertyRef("has_legal_hold")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AzureDataLakeFileSystemToStorageAccountRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AzureDataLakeFileSystemToStorageAccountRel(CartographyRelSchema):
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
class AzureDataLakeFileSystemSchema(CartographyNodeSchema):
    label: str = "AzureDataLakeFileSystem"
    properties: AzureDataLakeFileSystemProperties = AzureDataLakeFileSystemProperties()
    sub_resource_relationship: AzureDataLakeFileSystemToStorageAccountRel = (
        AzureDataLakeFileSystemToStorageAccountRel()
    )

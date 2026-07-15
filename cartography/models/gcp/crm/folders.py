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
class GCPFolderNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "name",
        description='The name of the folder, e.g. "folders/1234".',
    )  # Use full folder name as ID (e.g., "folders/1414")
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last time the node was updated.",
    )
    foldername: PropertyRef = PropertyRef(
        "name", description='The name of the folder, e.g. "folders/1234".'
    )
    displayname: PropertyRef = PropertyRef(
        "displayName", description='A friendly name of the folder, e.g. "My Folder".'
    )
    lifecyclestate: PropertyRef = PropertyRef(
        "lifecycleState",
        description="The folder's current lifecycle state. Assigned by the server.  See the [official docs](https://cloud.google.com/resource-manager/reference/rest/v2/folders#LifecycleState).",
    )
    parent_org: PropertyRef = PropertyRef(
        "parent_org",
        description='If the folder\'s parent is an organization, this field contains the organization ID, e.g. "organizations/1234".',
    )  # Will be set to org ID if parent is org
    parent_folder: PropertyRef = PropertyRef(
        "parent_folder",
        description='If the folder\'s parent is another folder, this field contains the folder ID, e.g. "folders/5678".',
    )  # Will be set to folder ID if parent is folder


@dataclass(frozen=True)
class GCPFolderToOrgParentRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last sync that observed this data.",
    )


@dataclass(frozen=True)
class GCPFolderToOrgParentRel(CartographyRelSchema):
    """Relationship when folder's parent is an organization"""

    target_node_label: str = "GCPOrganization"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("parent_org")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "PARENT"
    properties: GCPFolderToOrgParentRelProperties = GCPFolderToOrgParentRelProperties()


@dataclass(frozen=True)
class GCPFolderToFolderParentRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last sync that observed this data.",
    )


@dataclass(frozen=True)
class GCPFolderToFolderParentRel(CartographyRelSchema):
    """Relationship when folder's parent is another folder"""

    target_node_label: str = "GCPFolder"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("parent_folder")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "PARENT"
    properties: GCPFolderToFolderParentRelProperties = (
        GCPFolderToFolderParentRelProperties()
    )


@dataclass(frozen=True)
class GCPFolderToOrganizationRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last sync that observed this data.",
    )


@dataclass(frozen=True)
class GCPFolderToOrganizationRel(CartographyRelSchema):
    target_node_label: str = "GCPOrganization"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("ORG_RESOURCE_NAME", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: GCPFolderToOrganizationRelProperties = (
        GCPFolderToOrganizationRelProperties()
    )


@dataclass(frozen=True)
class GCPFolderSchema(CartographyNodeSchema):
    """A Google Cloud Folder resource."""

    label: str = "GCPFolder"
    properties: GCPFolderNodeProperties = GCPFolderNodeProperties()
    # Organization owns the folder as a resource
    sub_resource_relationship: GCPFolderToOrganizationRel = GCPFolderToOrganizationRel()
    other_relationships: OtherRelationships = OtherRelationships(
        [
            GCPFolderToOrgParentRel(),
            GCPFolderToFolderParentRel(),
        ]
    )

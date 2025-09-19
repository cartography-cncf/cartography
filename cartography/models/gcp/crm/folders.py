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
        "name"
    )  # Use full folder name as ID (e.g., "folders/1414")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    foldername: PropertyRef = PropertyRef("name")
    displayname: PropertyRef = PropertyRef("displayName")
    lifecyclestate: PropertyRef = PropertyRef("lifecycleState")
    parent_org: PropertyRef = PropertyRef(
        "parent_org"
    )  # Will be set to org ID if parent is org
    parent_folder: PropertyRef = PropertyRef(
        "parent_folder"
    )  # Will be set to folder ID if parent is folder


@dataclass(frozen=True)
class GCPFolderToOrgParentRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


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
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


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
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


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

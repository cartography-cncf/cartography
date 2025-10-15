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
class GCPProjectNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("projectId")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    projectnumber: PropertyRef = PropertyRef("projectNumber", extra_index=True)
    displayname: PropertyRef = PropertyRef("name")
    lifecyclestate: PropertyRef = PropertyRef("lifecycleState")
    parent_org: PropertyRef = PropertyRef(
        "parent_org"
    )  # Will be set to org ID if parent is org
    parent_folder: PropertyRef = PropertyRef(
        "parent_folder"
    )  # Will be set to folder ID if parent is folder


@dataclass(frozen=True)
class GCPProjectToOrgParentRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class GCPProjectToOrgParentRel(CartographyRelSchema):
    """Relationship when project's parent is an organization"""

    target_node_label: str = "GCPOrganization"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("parent_org")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "PARENT"
    properties: GCPProjectToOrgParentRelProperties = (
        GCPProjectToOrgParentRelProperties()
    )


@dataclass(frozen=True)
class GCPProjectToFolderParentRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class GCPProjectToFolderParentRel(CartographyRelSchema):
    """Relationship when project's parent is a folder"""

    target_node_label: str = "GCPFolder"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("parent_folder")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "PARENT"
    properties: GCPProjectToFolderParentRelProperties = (
        GCPProjectToFolderParentRelProperties()
    )


@dataclass(frozen=True)
class GCPProjectToOrganizationRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class GCPProjectToOrganizationRel(CartographyRelSchema):
    target_node_label: str = "GCPOrganization"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("ORG_RESOURCE_NAME", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: GCPProjectToOrganizationRelProperties = (
        GCPProjectToOrganizationRelProperties()
    )


@dataclass(frozen=True)
class GCPProjectSchema(CartographyNodeSchema):
    label: str = "GCPProject"
    properties: GCPProjectNodeProperties = GCPProjectNodeProperties()
    # Organization owns the project as a resource
    sub_resource_relationship: GCPProjectToOrganizationRel = (
        GCPProjectToOrganizationRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            GCPProjectToOrgParentRel(),
            GCPProjectToFolderParentRel(),
        ]
    )

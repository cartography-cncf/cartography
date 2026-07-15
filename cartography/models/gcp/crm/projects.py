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


@dataclass(frozen=True)
class GCPProjectNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "projectId", description="Stable identifier for this resource."
    )
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last sync that observed this data.",
    )
    projectnumber: PropertyRef = PropertyRef(
        "projectNumber",
        extra_index=True,
        description="Numeric identifier of the owning Google Cloud project.",
    )
    displayname: PropertyRef = PropertyRef(
        "name", description="Human-readable name shown for this resource."
    )
    lifecyclestate: PropertyRef = PropertyRef(
        "lifecycleState",
        description="Current Resource Manager project lifecycle state.",
    )
    parent_org: PropertyRef = PropertyRef(
        "parent_org",
        description="Parent organization resource name when the project belongs directly to an organization.",
    )  # Will be set to org ID if parent is org
    parent_folder: PropertyRef = PropertyRef(
        "parent_folder",
        description="Parent folder resource name when the project belongs to a folder.",
    )  # Will be set to folder ID if parent is folder


@dataclass(frozen=True)
class GCPProjectToOrgParentRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last sync that observed this data.",
    )


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
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last sync that observed this data.",
    )


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
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last sync that observed this data.",
    )


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
    """A Google Cloud Project resource."""

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
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(["Tenant"])

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
    projectid: PropertyRef = PropertyRef("projectId")
    projectnumber: PropertyRef = PropertyRef("projectNumber")
    displayname: PropertyRef = PropertyRef("name")
    lifecyclestate: PropertyRef = PropertyRef("lifecycleState")


@dataclass(frozen=True)
class GCPOrganizationToGCPProjectRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class GCPOrganizationToGCPProjectRel(CartographyRelSchema):
    # Represents the tenant relationship: (:GCPProject)<-[:RESOURCE]-(:GCPOrganization)
    target_node_label: str = "GCPOrganization"
    # Tenant id supplied via kwargs during load/cleanup to support scoped cleanup per org
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {
            "id": PropertyRef("ORG_ID", set_in_kwargs=True),
        }
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: GCPOrganizationToGCPProjectRelProperties = (
        GCPOrganizationToGCPProjectRelProperties()
    )


@dataclass(frozen=True)
class GCPFolderToGCPProjectRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class GCPFolderToGCPProjectRel(CartographyRelSchema):
    target_node_label: str = "GCPFolder"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {
            "id": PropertyRef("parent_folder"),
        }
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: GCPFolderToGCPProjectRelProperties = (
        GCPFolderToGCPProjectRelProperties()
    )


@dataclass(frozen=True)
class GCPProjectSchema(CartographyNodeSchema):
    label: str = "GCPProject"
    properties: GCPProjectNodeProperties = GCPProjectNodeProperties()
    # Organization is the tenant-like object for Projects
    sub_resource_relationship: GCPOrganizationToGCPProjectRel = (
        GCPOrganizationToGCPProjectRel()
    )
    # Folders indicate placement within the hierarchy and are modeled as an additional relationship
    other_relationships: OtherRelationships = OtherRelationships(
        [
            GCPFolderToGCPProjectRel(),
        ]
    )

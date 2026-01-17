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
class AirbyteUserNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id")
    name: PropertyRef = PropertyRef("name")
    email: PropertyRef = PropertyRef("email", extra_index=True)
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AirbyteUserToOrganizationRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:AirbyteOrganization)-[:RESOURCE]->(:AirbyteUser)
class AirbyteUserToOrganizationRel(CartographyRelSchema):
    target_node_label: str = "AirbyteOrganization"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("ORG_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: AirbyteUserToOrganizationRelProperties = (
        AirbyteUserToOrganizationRelProperties()
    )


@dataclass(frozen=True)
class AirbyteUserToOrganizationAdminRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:AirbyteOrganization)<-[:ADMIN_OF]-(:AirbyteUser)
class AirbyteUserToOrganizationAdminRel(CartographyRelSchema):
    target_node_label: str = "AirbyteOrganization"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("adminOfOrganization", one_to_many=True)},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "ADMIN_OF"
    properties: AirbyteUserToOrganizationAdminRelProperties = (
        AirbyteUserToOrganizationAdminRelProperties()
    )


@dataclass(frozen=True)
class AirbyteUserToWorkspaceAdminRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:AirbyteWorkspace)<-[:ADMIN_OF]-(:AirbyteUser)
class AirbyteUserToWorkspaceAdminRel(CartographyRelSchema):
    target_node_label: str = "AirbyteWorkspace"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("adminOfWorkspace", one_to_many=True)},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "ADMIN_OF"
    properties: AirbyteUserToWorkspaceAdminRelProperties = (
        AirbyteUserToWorkspaceAdminRelProperties()
    )


@dataclass(frozen=True)
class AirbyteUserToWorkspaceMemberRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:AirbyteWorkspace)<-[:MEMBER_OF]-(:AirbyteUser)
class AirbyteUserToWorkspaceMemberRel(CartographyRelSchema):
    target_node_label: str = "AirbyteWorkspace"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("memberOfWorkspace", one_to_many=True)},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "MEMBER_OF"
    properties: AirbyteUserToWorkspaceMemberRelProperties = (
        AirbyteUserToWorkspaceMemberRelProperties()
    )


@dataclass(frozen=True)
class AirbyteUserSchema(CartographyNodeSchema):
    label: str = "AirbyteUser"
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(
        ["UserAccount"]
    )  # UserAccount label is used for ontology mapping
    properties: AirbyteUserNodeProperties = AirbyteUserNodeProperties()
    sub_resource_relationship: AirbyteUserToOrganizationRel = (
        AirbyteUserToOrganizationRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            AirbyteUserToOrganizationAdminRel(),
            AirbyteUserToWorkspaceAdminRel(),
            AirbyteUserToWorkspaceMemberRel(),
        ]
    )

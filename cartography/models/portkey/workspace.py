from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.nodes import ExtraNodeLabels
from cartography.models.core.relationships import CartographyRelProperties
from cartography.models.core.relationships import CartographyRelSchema
from cartography.models.core.relationships import LinkDirection
from cartography.models.core.relationships import SourceNodeMatcher
from cartography.models.core.relationships import TargetNodeMatcher
from cartography.models.core.relationships import make_source_node_matcher
from cartography.models.core.relationships import make_target_node_matcher


@dataclass(frozen=True)
class PortkeyWorkspaceNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id")
    object: PropertyRef = PropertyRef("object")
    slug: PropertyRef = PropertyRef("slug")
    name: PropertyRef = PropertyRef("name")
    description: PropertyRef = PropertyRef("description")
    created_at: PropertyRef = PropertyRef("created_at")
    last_updated_at: PropertyRef = PropertyRef("last_updated_at")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class PortkeyWorkspaceToOrganizationRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class PortkeyWorkspaceToOrganizationRel(CartographyRelSchema):
    target_node_label: str = "PortkeyOrganization"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("PORTKEY_ORG_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: PortkeyWorkspaceToOrganizationRelProperties = (
        PortkeyWorkspaceToOrganizationRelProperties()
    )


@dataclass(frozen=True)
class PortkeyWorkspaceSchema(CartographyNodeSchema):
    label: str = "PortkeyWorkspace"
    properties: PortkeyWorkspaceNodeProperties = PortkeyWorkspaceNodeProperties()
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(["Tenant"])
    sub_resource_relationship: PortkeyWorkspaceToOrganizationRel = (
        PortkeyWorkspaceToOrganizationRel()
    )


@dataclass(frozen=True)
class PortkeyUserWorkspaceMembershipRelProperties(CartographyRelProperties):
    role: PropertyRef = PropertyRef("role")
    org_role: PropertyRef = PropertyRef("org_role")
    status: PropertyRef = PropertyRef("status")
    created_at: PropertyRef = PropertyRef("created_at")
    last_updated_at: PropertyRef = PropertyRef("last_updated_at")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    _sub_resource_label: PropertyRef = PropertyRef(
        "_sub_resource_label", set_in_kwargs=True
    )
    _sub_resource_id: PropertyRef = PropertyRef("_sub_resource_id", set_in_kwargs=True)


@dataclass(frozen=True)
class PortkeyUserWorkspaceMembershipMatchLink(CartographyRelSchema):
    source_node_label: str = "PortkeyUser"
    source_node_matcher: SourceNodeMatcher = make_source_node_matcher(
        {"id": PropertyRef("user_id")},
    )
    target_node_label: str = "PortkeyWorkspace"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("workspace_id")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "MEMBER_OF"
    properties: PortkeyUserWorkspaceMembershipRelProperties = (
        PortkeyUserWorkspaceMembershipRelProperties()
    )

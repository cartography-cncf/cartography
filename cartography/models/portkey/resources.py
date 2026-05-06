from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.nodes import ExtraNodeLabels
from cartography.models.core.relationships import CartographyRelProperties
from cartography.models.core.relationships import CartographyRelSchema
from cartography.models.core.relationships import LinkDirection
from cartography.models.core.relationships import OtherRelationships
from cartography.models.core.relationships import TargetNodeMatcher
from cartography.models.core.relationships import make_target_node_matcher


@dataclass(frozen=True)
class _OrgResourceRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class _PortkeyResourceToOrganizationRel(CartographyRelSchema):
    target_node_label: str = "PortkeyOrganization"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("PORTKEY_ORG_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: _OrgResourceRelProperties = _OrgResourceRelProperties()


@dataclass(frozen=True)
class _WorkspaceRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class _ResourceToWorkspaceRel(CartographyRelSchema):
    target_node_label: str = "PortkeyWorkspace"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("workspace_id")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: _WorkspaceRelProperties = _WorkspaceRelProperties()


@dataclass(frozen=True)
class _AvailableInWorkspaceRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class _AvailableInWorkspaceRel(CartographyRelSchema):
    target_node_label: str = "PortkeyWorkspace"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("workspace_id")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "AVAILABLE_IN"
    properties: _AvailableInWorkspaceRelProperties = (
        _AvailableInWorkspaceRelProperties()
    )


@dataclass(frozen=True)
class _UserOwnsRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class _ResourceToUserOwnsRel(CartographyRelSchema):
    target_node_label: str = "PortkeyUser"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("user_id")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "OWNS"
    properties: _UserOwnsRelProperties = _UserOwnsRelProperties()


@dataclass(frozen=True)
class _InvitedByRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class _InviteToInviterRel(CartographyRelSchema):
    target_node_label: str = "PortkeyUser"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("invited_by")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "INVITED_BY"
    properties: _InvitedByRelProperties = _InvitedByRelProperties()


@dataclass(frozen=True)
class _InviteToWorkspaceRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class _InviteToWorkspaceRel(CartographyRelSchema):
    target_node_label: str = "PortkeyWorkspace"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("workspace_ids", one_to_many=True)},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "INVITED_TO"
    properties: _InviteToWorkspaceRelProperties = _InviteToWorkspaceRelProperties()


@dataclass(frozen=True)
class _UpdatedByRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class _ResourceToUpdatedByUserRel(CartographyRelSchema):
    target_node_label: str = "PortkeyUser"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("updated_by")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "UPDATED_BY"
    properties: _UpdatedByRelProperties = _UpdatedByRelProperties()


@dataclass(frozen=True)
class _OwnerRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class _ResourceToOwnerUserRel(CartographyRelSchema):
    target_node_label: str = "PortkeyUser"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("owner_id")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "OWNS"
    properties: _OwnerRelProperties = _OwnerRelProperties()


@dataclass(frozen=True)
class _PromptToCollectionRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class _PromptToCollectionRel(CartographyRelSchema):
    target_node_label: str = "PortkeyPromptCollection"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("collection_id")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "MEMBER_OF"
    properties: _PromptToCollectionRelProperties = _PromptToCollectionRelProperties()


@dataclass(frozen=True)
class _CollectionToParentCollectionRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class _CollectionToParentCollectionRel(CartographyRelSchema):
    target_node_label: str = "PortkeyPromptCollection"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("parent_collection_id")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "PART_OF"
    properties: _CollectionToParentCollectionRelProperties = (
        _CollectionToParentCollectionRelProperties()
    )


@dataclass(frozen=True)
class _ProviderToIntegrationRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class _ProviderToIntegrationRel(CartographyRelSchema):
    target_node_label: str = "PortkeyIntegration"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("integration_id")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "USES"
    properties: _ProviderToIntegrationRelProperties = _ProviderToIntegrationRelProperties()


@dataclass(frozen=True)
class _IntegrationToSecretReferenceRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class _IntegrationToSecretReferenceRel(CartographyRelSchema):
    target_node_label: str = "PortkeySecretReference"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("secret_reference_ids", one_to_many=True)},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "USES_SECRET"
    properties: _IntegrationToSecretReferenceRelProperties = (
        _IntegrationToSecretReferenceRelProperties()
    )


@dataclass(frozen=True)
class _MCPServerToIntegrationRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class _MCPServerToIntegrationRel(CartographyRelSchema):
    target_node_label: str = "PortkeyMCPIntegration"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("mcp_integration_id")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "USES"
    properties: _MCPServerToIntegrationRelProperties = (
        _MCPServerToIntegrationRelProperties()
    )


@dataclass(frozen=True)
class PortkeyInviteNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id")
    object: PropertyRef = PropertyRef("object")
    email: PropertyRef = PropertyRef("email", extra_index=True)
    role: PropertyRef = PropertyRef("role")
    status: PropertyRef = PropertyRef("status")
    created_at: PropertyRef = PropertyRef("created_at")
    expires_at: PropertyRef = PropertyRef("expires_at")
    accepted_at: PropertyRef = PropertyRef("accepted_at")
    workspaces_json: PropertyRef = PropertyRef("workspaces_json")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class PortkeyInviteSchema(CartographyNodeSchema):
    label: str = "PortkeyInvite"
    properties: PortkeyInviteNodeProperties = PortkeyInviteNodeProperties()
    sub_resource_relationship: _PortkeyResourceToOrganizationRel = (
        _PortkeyResourceToOrganizationRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [_InviteToInviterRel(), _InviteToWorkspaceRel()],
    )


@dataclass(frozen=True)
class PortkeyAPIKeyNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id")
    object: PropertyRef = PropertyRef("object")
    key: PropertyRef = PropertyRef("key")
    name: PropertyRef = PropertyRef("name")
    description: PropertyRef = PropertyRef("description")
    type: PropertyRef = PropertyRef("type")
    status: PropertyRef = PropertyRef("status")
    created_at: PropertyRef = PropertyRef("created_at")
    last_updated_at: PropertyRef = PropertyRef("last_updated_at")
    creation_mode: PropertyRef = PropertyRef("creation_mode")
    expires_at: PropertyRef = PropertyRef("expires_at")
    scopes: PropertyRef = PropertyRef("scopes")
    alert_emails: PropertyRef = PropertyRef("alert_emails")
    reset_usage: PropertyRef = PropertyRef("reset_usage")
    rate_limits_json: PropertyRef = PropertyRef("rate_limits_json")
    usage_limits_json: PropertyRef = PropertyRef("usage_limits_json")
    defaults_json: PropertyRef = PropertyRef("defaults_json")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class PortkeyAPIKeySchema(CartographyNodeSchema):
    label: str = "PortkeyAPIKey"
    properties: PortkeyAPIKeyNodeProperties = PortkeyAPIKeyNodeProperties()
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(["APIKey"])
    sub_resource_relationship: _PortkeyResourceToOrganizationRel = (
        _PortkeyResourceToOrganizationRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [_AvailableInWorkspaceRel(), _ResourceToUserOwnsRel()],
    )


@dataclass(frozen=True)
class PortkeyVirtualKeyNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id")
    object: PropertyRef = PropertyRef("object")
    slug: PropertyRef = PropertyRef("slug")
    name: PropertyRef = PropertyRef("name")
    note: PropertyRef = PropertyRef("note")
    status: PropertyRef = PropertyRef("status")
    created_at: PropertyRef = PropertyRef("created_at")
    expires_at: PropertyRef = PropertyRef("expires_at")
    reset_usage: PropertyRef = PropertyRef("reset_usage")
    model_config_json: PropertyRef = PropertyRef("model_config_json")
    rate_limits_json: PropertyRef = PropertyRef("rate_limits_json")
    usage_limits_json: PropertyRef = PropertyRef("usage_limits_json")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class PortkeyVirtualKeySchema(CartographyNodeSchema):
    label: str = "PortkeyVirtualKey"
    properties: PortkeyVirtualKeyNodeProperties = PortkeyVirtualKeyNodeProperties()
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(["APIKey"])
    sub_resource_relationship: _PortkeyResourceToOrganizationRel = (
        _PortkeyResourceToOrganizationRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [_AvailableInWorkspaceRel()],
    )


@dataclass(frozen=True)
class PortkeyConfigNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id")
    name: PropertyRef = PropertyRef("name")
    slug: PropertyRef = PropertyRef("slug")
    organisation_id: PropertyRef = PropertyRef("organisation_id")
    workspace_id: PropertyRef = PropertyRef("workspace_id")
    is_default: PropertyRef = PropertyRef("is_default")
    status: PropertyRef = PropertyRef("status")
    owner_id: PropertyRef = PropertyRef("owner_id")
    updated_by: PropertyRef = PropertyRef("updated_by")
    created_at: PropertyRef = PropertyRef("created_at")
    last_updated_at: PropertyRef = PropertyRef("last_updated_at")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class PortkeyConfigSchema(CartographyNodeSchema):
    label: str = "PortkeyConfig"
    properties: PortkeyConfigNodeProperties = PortkeyConfigNodeProperties()
    scoped_cleanup: bool = False
    other_relationships: OtherRelationships = OtherRelationships(
        [_ResourceToWorkspaceRel(), _ResourceToOwnerUserRel(), _ResourceToUpdatedByUserRel()],
    )


@dataclass(frozen=True)
class PortkeyIntegrationNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id")
    object: PropertyRef = PropertyRef("object")
    organisation_id: PropertyRef = PropertyRef("organisation_id")
    workspace_id: PropertyRef = PropertyRef("workspace_id")
    ai_provider_id: PropertyRef = PropertyRef("ai_provider_id")
    name: PropertyRef = PropertyRef("name")
    slug: PropertyRef = PropertyRef("slug")
    description: PropertyRef = PropertyRef("description")
    status: PropertyRef = PropertyRef("status")
    created_at: PropertyRef = PropertyRef("created_at")
    last_updated_at: PropertyRef = PropertyRef("last_updated_at")
    secret_mappings_json: PropertyRef = PropertyRef("secret_mappings_json")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class PortkeyIntegrationSchema(CartographyNodeSchema):
    label: str = "PortkeyIntegration"
    properties: PortkeyIntegrationNodeProperties = PortkeyIntegrationNodeProperties()
    sub_resource_relationship: _PortkeyResourceToOrganizationRel = (
        _PortkeyResourceToOrganizationRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [_IntegrationToSecretReferenceRel()],
    )


@dataclass(frozen=True)
class PortkeyProviderNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id")
    object: PropertyRef = PropertyRef("object")
    slug: PropertyRef = PropertyRef("slug")
    name: PropertyRef = PropertyRef("name")
    note: PropertyRef = PropertyRef("note")
    status: PropertyRef = PropertyRef("status")
    integration_id: PropertyRef = PropertyRef("integration_id")
    workspace_id: PropertyRef = PropertyRef("workspace_id")
    created_at: PropertyRef = PropertyRef("created_at")
    expires_at: PropertyRef = PropertyRef("expires_at")
    reset_usage: PropertyRef = PropertyRef("reset_usage")
    rate_limits_json: PropertyRef = PropertyRef("rate_limits_json")
    usage_limits_json: PropertyRef = PropertyRef("usage_limits_json")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class PortkeyProviderSchema(CartographyNodeSchema):
    label: str = "PortkeyProvider"
    properties: PortkeyProviderNodeProperties = PortkeyProviderNodeProperties()
    sub_resource_relationship: _PortkeyResourceToOrganizationRel = (
        _PortkeyResourceToOrganizationRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [_AvailableInWorkspaceRel(), _ProviderToIntegrationRel()],
    )


@dataclass(frozen=True)
class PortkeyGuardrailNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id")
    name: PropertyRef = PropertyRef("name")
    slug: PropertyRef = PropertyRef("slug")
    organisation_id: PropertyRef = PropertyRef("organisation_id")
    workspace_id: PropertyRef = PropertyRef("workspace_id")
    status: PropertyRef = PropertyRef("status")
    created_at: PropertyRef = PropertyRef("created_at")
    last_updated_at: PropertyRef = PropertyRef("last_updated_at")
    owner_id: PropertyRef = PropertyRef("owner_id")
    updated_by: PropertyRef = PropertyRef("updated_by")
    checks_json: PropertyRef = PropertyRef("checks_json")
    actions_json: PropertyRef = PropertyRef("actions_json")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class PortkeyGuardrailSchema(CartographyNodeSchema):
    label: str = "PortkeyGuardrail"
    properties: PortkeyGuardrailNodeProperties = PortkeyGuardrailNodeProperties()
    scoped_cleanup: bool = False
    other_relationships: OtherRelationships = OtherRelationships(
        [_ResourceToWorkspaceRel(), _ResourceToOwnerUserRel(), _ResourceToUpdatedByUserRel()],
    )


@dataclass(frozen=True)
class PortkeyMCPIntegrationNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id")
    name: PropertyRef = PropertyRef("name")
    owner_id: PropertyRef = PropertyRef("owner_id")
    status: PropertyRef = PropertyRef("status")
    type: PropertyRef = PropertyRef("type")
    url: PropertyRef = PropertyRef("url")
    auth_type: PropertyRef = PropertyRef("auth_type")
    transport: PropertyRef = PropertyRef("transport")
    configurations_json: PropertyRef = PropertyRef("configurations_json")
    created_at: PropertyRef = PropertyRef("created_at")
    last_updated_at: PropertyRef = PropertyRef("last_updated_at")
    slug: PropertyRef = PropertyRef("slug")
    workspace_id: PropertyRef = PropertyRef("workspace_id")
    description: PropertyRef = PropertyRef("description")
    workspaces_count: PropertyRef = PropertyRef("workspaces_count")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class PortkeyMCPIntegrationSchema(CartographyNodeSchema):
    label: str = "PortkeyMCPIntegration"
    properties: PortkeyMCPIntegrationNodeProperties = (
        PortkeyMCPIntegrationNodeProperties()
    )
    sub_resource_relationship: _PortkeyResourceToOrganizationRel = (
        _PortkeyResourceToOrganizationRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [_ResourceToWorkspaceRel(), _ResourceToOwnerUserRel()],
    )


@dataclass(frozen=True)
class PortkeyMCPServerNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id")
    organisation_id: PropertyRef = PropertyRef("organisation_id")
    name: PropertyRef = PropertyRef("name")
    description: PropertyRef = PropertyRef("description")
    status: PropertyRef = PropertyRef("status")
    created_at: PropertyRef = PropertyRef("created_at")
    owner_id: PropertyRef = PropertyRef("owner_id")
    slug: PropertyRef = PropertyRef("slug")
    workspace_id: PropertyRef = PropertyRef("workspace_id")
    mcp_integration_id: PropertyRef = PropertyRef("mcp_integration_id")
    mcp_integration_slug: PropertyRef = PropertyRef("mcp_integration_slug")
    mcp_integration_url: PropertyRef = PropertyRef("mcp_integration_url")
    auth_type: PropertyRef = PropertyRef("auth_type")
    workspace_name: PropertyRef = PropertyRef("workspace_name")
    workspace_slug: PropertyRef = PropertyRef("workspace_slug")
    url: PropertyRef = PropertyRef("url")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class PortkeyMCPServerSchema(CartographyNodeSchema):
    label: str = "PortkeyMCPServer"
    properties: PortkeyMCPServerNodeProperties = PortkeyMCPServerNodeProperties()
    scoped_cleanup: bool = False
    other_relationships: OtherRelationships = OtherRelationships(
        [_ResourceToWorkspaceRel(), _ResourceToOwnerUserRel(), _MCPServerToIntegrationRel()],
    )


@dataclass(frozen=True)
class PortkeyPromptCollectionNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id")
    name: PropertyRef = PropertyRef("name")
    workspace_id: PropertyRef = PropertyRef("workspace_id")
    slug: PropertyRef = PropertyRef("slug")
    parent_collection_id: PropertyRef = PropertyRef("parent_collection_id")
    is_default: PropertyRef = PropertyRef("is_default")
    status: PropertyRef = PropertyRef("status")
    created_at: PropertyRef = PropertyRef("created_at")
    last_updated_at: PropertyRef = PropertyRef("last_updated_at")
    collection_details_json: PropertyRef = PropertyRef("collection_details_json")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class PortkeyPromptCollectionSchema(CartographyNodeSchema):
    label: str = "PortkeyPromptCollection"
    properties: PortkeyPromptCollectionNodeProperties = (
        PortkeyPromptCollectionNodeProperties()
    )
    scoped_cleanup: bool = False
    other_relationships: OtherRelationships = OtherRelationships(
        [_ResourceToWorkspaceRel(), _CollectionToParentCollectionRel()],
    )


@dataclass(frozen=True)
class PortkeyPromptNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id")
    object: PropertyRef = PropertyRef("object")
    slug: PropertyRef = PropertyRef("slug")
    name: PropertyRef = PropertyRef("name")
    collection_id: PropertyRef = PropertyRef("collection_id")
    workspace_id: PropertyRef = PropertyRef("workspace_id")
    model: PropertyRef = PropertyRef("model")
    status: PropertyRef = PropertyRef("status")
    created_at: PropertyRef = PropertyRef("created_at")
    last_updated_at: PropertyRef = PropertyRef("last_updated_at")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class PortkeyPromptSchema(CartographyNodeSchema):
    label: str = "PortkeyPrompt"
    properties: PortkeyPromptNodeProperties = PortkeyPromptNodeProperties()
    scoped_cleanup: bool = False
    other_relationships: OtherRelationships = OtherRelationships(
        [_ResourceToWorkspaceRel(), _PromptToCollectionRel()],
    )


@dataclass(frozen=True)
class PortkeySecretReferenceNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id")
    object: PropertyRef = PropertyRef("object")
    slug: PropertyRef = PropertyRef("slug")
    name: PropertyRef = PropertyRef("name")
    description: PropertyRef = PropertyRef("description")
    manager_type: PropertyRef = PropertyRef("manager_type")
    secret_path: PropertyRef = PropertyRef("secret_path")
    secret_key: PropertyRef = PropertyRef("secret_key")
    status: PropertyRef = PropertyRef("status")
    allow_all_workspaces: PropertyRef = PropertyRef("allow_all_workspaces")
    auth_config_json: PropertyRef = PropertyRef("auth_config_json")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class PortkeySecretReferenceSchema(CartographyNodeSchema):
    label: str = "PortkeySecretReference"
    properties: PortkeySecretReferenceNodeProperties = (
        PortkeySecretReferenceNodeProperties()
    )
    sub_resource_relationship: _PortkeyResourceToOrganizationRel = (
        _PortkeyResourceToOrganizationRel()
    )

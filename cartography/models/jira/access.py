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
from cartography.models.ontology.labels import TENANT
from cartography.models.ontology.labels import USER_ACCOUNT


@dataclass(frozen=True)
class JiraRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class JiraResourceRel(CartographyRelSchema):
    """The Jira Cloud tenant contains this resource."""

    target_node_label: str = "JiraTenant"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("TENANT_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: JiraRelProperties = JiraRelProperties()


@dataclass(frozen=True)
class JiraGroupAdminRel(CartographyRelSchema):
    """An admin or site-admin group reported by Jira group accessType."""

    target_node_label: str = "JiraTenant"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("admin_tenant_id")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "ADMIN_OF"
    properties: JiraRelProperties = JiraRelProperties()


@dataclass(frozen=True)
class JiraUserGroupRel(CartographyRelSchema):
    """A user belongs to this group, including inactive memberships."""

    target_node_label: str = "JiraGroup"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("group_ids", one_to_many=True)},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "MEMBER_OF"
    properties: JiraRelProperties = JiraRelProperties()


@dataclass(frozen=True)
class JiraProjectLeadRel(CartographyRelSchema):
    """The user is the project lead; this alone does not grant permissions."""

    target_node_label: str = "JiraUser"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("lead_id")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "LEADS"
    properties: JiraRelProperties = JiraRelProperties()


@dataclass(frozen=True)
class JiraRoleProjectRel(CartographyRelSchema):
    """The role assignment belongs to this project."""

    target_node_label: str = "JiraProject"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("project_id")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "ROLE_OF"
    properties: JiraRelProperties = JiraRelProperties()


@dataclass(frozen=True)
class JiraRoleUserRel(CartographyRelSchema):
    """A user is a direct actor in this project role."""

    target_node_label: str = "JiraUser"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("user_ids", one_to_many=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "MEMBER_OF"
    properties: JiraRelProperties = JiraRelProperties()


@dataclass(frozen=True)
class JiraRoleGroupRel(CartographyRelSchema):
    """A group is an actor in this project role."""

    target_node_label: str = "JiraGroup"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("group_ids", one_to_many=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "MEMBER_OF"
    properties: JiraRelProperties = JiraRelProperties()


@dataclass(frozen=True)
class JiraGrantProjectRel(CartographyRelSchema):
    """This configured permission grant applies to the project."""

    target_node_label: str = "JiraProject"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("project_id")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "APPLIES_TO"
    properties: JiraRelProperties = JiraRelProperties()


@dataclass(frozen=True)
class JiraGrantUserRel(CartographyRelSchema):
    """The principal is the configured holder of this permission grant."""

    target_node_label: str = "JiraUser"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("user_id")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "HAS_PERMISSION"
    properties: JiraRelProperties = JiraRelProperties()


@dataclass(frozen=True)
class JiraGrantGroupRel(CartographyRelSchema):
    """The principal is the configured holder of this permission grant."""

    target_node_label: str = "JiraGroup"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("group_id")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "HAS_PERMISSION"
    properties: JiraRelProperties = JiraRelProperties()


@dataclass(frozen=True)
class JiraGrantProjectRoleRel(CartographyRelSchema):
    """The principal is the configured holder of this permission grant."""

    target_node_label: str = "JiraProjectRole"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("role_id")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "HAS_PERMISSION"
    properties: JiraRelProperties = JiraRelProperties()


@dataclass(frozen=True)
class JiraTenantProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "id", description="Stable Cloud UUID supplied by --jira-cloud-id."
    )
    name: PropertyRef = PropertyRef("name", description="serverInfo.serverTitle.")
    url: PropertyRef = PropertyRef("url", description="serverInfo.baseUrl.")
    domain: PropertyRef = PropertyRef(
        "domain", description="Hostname parsed from serverInfo.baseUrl."
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class JiraTenantSchema(CartographyNodeSchema):
    """A Jira Cloud site with the Tenant ontology label."""

    label: str = "JiraTenant"
    properties: JiraTenantProperties = JiraTenantProperties()
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels([TENANT])


@dataclass(frozen=True)
class JiraGroupProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "id", description="Cloud ID, group kind, and URL-escaped groupId."
    )
    group_id: PropertyRef = PropertyRef(
        "group_id", description="group/bulk groupId, independent of group name."
    )
    name: PropertyRef = PropertyRef("name", description="group/bulk name.")
    admin_access_types: PropertyRef = PropertyRef(
        "admin_access_types",
        description="Experimental group/bulk accessType filters matching this group: admin or site-admin; not exhaustive effective privileges.",
    )
    tenant_id: PropertyRef = PropertyRef(
        "TENANT_ID", set_in_kwargs=True, description="Jira Cloud ID."
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class JiraGroupSchema(CartographyNodeSchema):
    """A Jira group and its API-reported administrative access levels."""

    label: str = "JiraGroup"
    properties: JiraGroupProperties = JiraGroupProperties()
    sub_resource_relationship: JiraResourceRel = JiraResourceRel()
    other_relationships: OtherRelationships = OtherRelationships([JiraGroupAdminRel()])


@dataclass(frozen=True)
class JiraUserProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "id", description="Cloud ID, user kind, and URL-escaped accountId."
    )
    account_id: PropertyRef = PropertyRef(
        "account_id",
        description="Atlassian accountId from a user profile or actor/holder reference.",
    )
    display_name: PropertyRef = PropertyRef(
        "display_name",
        description="User profile displayName, subject to profile visibility.",
    )
    email: PropertyRef = PropertyRef(
        "email",
        description="User profile emailAddress if visible; absent addresses are not inferred.",
    )
    active: PropertyRef = PropertyRef(
        "active",
        extra_index=True,
        description="User profile active flag; absent for reference-only accounts.",
    )
    account_type: PropertyRef = PropertyRef(
        "account_type",
        description="User profile accountType: atlassian, app, customer, or unknown; absent for reference-only accounts.",
    )
    tenant_id: PropertyRef = PropertyRef(
        "TENANT_ID", set_in_kwargs=True, description="Jira Cloud ID."
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class JiraUserSchema(CartographyNodeSchema):
    """A Jira account. Atlassian human accounts carry the UserAccount ontology label."""

    label: str = "JiraUser"
    properties: JiraUserProperties = JiraUserProperties()
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(
        [USER_ACCOUNT.when(account_type="atlassian")]
    )
    sub_resource_relationship: JiraResourceRel = JiraResourceRel()
    other_relationships: OtherRelationships = OtherRelationships([JiraUserGroupRel()])


@dataclass(frozen=True)
class JiraProjectProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "id", description="Cloud ID, project kind, and URL-escaped project id."
    )
    project_id: PropertyRef = PropertyRef(
        "project_id", description="project/search id."
    )
    key: PropertyRef = PropertyRef("key", description="project/search key; mutable.")
    name: PropertyRef = PropertyRef("name", description="project/search name.")
    project_type: PropertyRef = PropertyRef(
        "project_type", description="project/search projectTypeKey."
    )
    style: PropertyRef = PropertyRef(
        "style", description="project/search style: classic or next-gen (team-managed)."
    )
    permission_scheme_id: PropertyRef = PropertyRef(
        "permission_scheme_id",
        description="project/{id}/permissionscheme id for company-managed projects.",
    )
    permission_scheme_supported: PropertyRef = PropertyRef(
        "permission_scheme_supported",
        description="Derived from style; false for next-gen projects, whose scheme grants are not exported.",
    )
    tenant_id: PropertyRef = PropertyRef(
        "TENANT_ID", set_in_kwargs=True, description="Jira Cloud ID."
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class JiraProjectSchema(CartographyNodeSchema):
    """A live Jira project; permission grants describe configuration, not effective issue access."""

    label: str = "JiraProject"
    properties: JiraProjectProperties = JiraProjectProperties()
    sub_resource_relationship: JiraResourceRel = JiraResourceRel()
    other_relationships: OtherRelationships = OtherRelationships([JiraProjectLeadRel()])


@dataclass(frozen=True)
class JiraProjectRoleProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "id", description="Cloud ID, role kind, and URL-escaped project and role IDs."
    )
    role_id: PropertyRef = PropertyRef(
        "role_id",
        description="project/{id}/role/{roleId} id; assignments are scoped to the project.",
    )
    name: PropertyRef = PropertyRef("name", description="Project role name.")
    description: PropertyRef = PropertyRef(
        "description", description="Project role description."
    )
    admin: PropertyRef = PropertyRef(
        "admin",
        description="Project role admin flag; does not infer effective permissions.",
    )
    tenant_id: PropertyRef = PropertyRef(
        "TENANT_ID", set_in_kwargs=True, description="Jira Cloud ID."
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class JiraProjectRoleSchema(CartographyNodeSchema):
    """A project-scoped role with its user and group actors. Membership alone does not grant access."""

    label: str = "JiraProjectRole"
    properties: JiraProjectRoleProperties = JiraProjectRoleProperties()
    sub_resource_relationship: JiraResourceRel = JiraResourceRel()
    other_relationships: OtherRelationships = OtherRelationships(
        [JiraRoleProjectRel(), JiraRoleUserRel(), JiraRoleGroupRel()]
    )


@dataclass(frozen=True)
class JiraPermissionGrantProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "id",
        description="Cloud ID, grant kind, and URL-escaped project, scheme, and grant IDs.",
    )
    grant_id: PropertyRef = PropertyRef(
        "grant_id",
        description="permissionscheme/{id} permissions[].id within the scheme.",
    )
    scheme_id: PropertyRef = PropertyRef(
        "scheme_id", description="Assigned permissionscheme id."
    )
    permission: PropertyRef = PropertyRef(
        "permission",
        extra_index=True,
        description="permissions[].permission, such as BROWSE_PROJECTS or ADMINISTER_PROJECTS.",
    )
    holder_type: PropertyRef = PropertyRef(
        "holder_type",
        description="permissions[].holder.type, including conditional or app-specific holders.",
    )
    holder_parameter: PropertyRef = PropertyRef(
        "holder_parameter",
        description="Original permissions[].holder.parameter, such as group name or role ID.",
    )
    holder_value: PropertyRef = PropertyRef(
        "holder_value",
        description="Original permissions[].holder.value, such as group ID.",
    )
    tenant_id: PropertyRef = PropertyRef(
        "TENANT_ID", set_in_kwargs=True, description="Jira Cloud ID."
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class JiraPermissionGrantSchema(CartographyNodeSchema):
    """A permission-scheme grant applied to a project. Conditional holder types remain explicit without invented effective-access edges."""

    label: str = "JiraPermissionGrant"
    properties: JiraPermissionGrantProperties = JiraPermissionGrantProperties()
    sub_resource_relationship: JiraResourceRel = JiraResourceRel()
    other_relationships: OtherRelationships = OtherRelationships(
        [
            JiraGrantProjectRel(),
            JiraGrantUserRel(),
            JiraGrantGroupRel(),
            JiraGrantProjectRoleRel(),
        ]
    )

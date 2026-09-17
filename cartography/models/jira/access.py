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
        "id", description="Tenant-scoped stable resource identifier."
    )
    name: PropertyRef = PropertyRef("name", description="Site title.")
    url: PropertyRef = PropertyRef("url", description="Site base URL.")
    domain: PropertyRef = PropertyRef("domain", description="Site hostname.")
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
        "id", description="Tenant-scoped stable resource identifier."
    )
    group_id: PropertyRef = PropertyRef(
        "group_id", description="Atlassian group ID, independent of group name."
    )
    name: PropertyRef = PropertyRef("name", description="Group name.")
    admin_access_types: PropertyRef = PropertyRef(
        "admin_access_types",
        description="Access levels returned by group/bulk: admin or site-admin.",
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
        "id", description="Tenant-scoped stable resource identifier."
    )
    account_id: PropertyRef = PropertyRef(
        "account_id", description="Atlassian account ID."
    )
    display_name: PropertyRef = PropertyRef(
        "display_name", description="Display name subject to profile visibility."
    )
    email: PropertyRef = PropertyRef(
        "email",
        description="Email address if visible; absent addresses are not inferred.",
    )
    active: PropertyRef = PropertyRef(
        "active", description="Whether the Atlassian account is active."
    )
    account_type: PropertyRef = PropertyRef(
        "account_type",
        description="Atlassian account type: atlassian, app, customer, or unknown.",
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
        "id", description="Tenant-scoped stable resource identifier."
    )
    project_id: PropertyRef = PropertyRef("project_id", description="Jira project ID.")
    key: PropertyRef = PropertyRef("key", description="Mutable project key.")
    name: PropertyRef = PropertyRef("name", description="Project name.")
    project_type: PropertyRef = PropertyRef(
        "project_type", description="Jira project product type."
    )
    style: PropertyRef = PropertyRef(
        "style", description="classic or next-gen (team-managed)."
    )
    permission_scheme_id: PropertyRef = PropertyRef(
        "permission_scheme_id",
        description="Assigned permission scheme ID for company-managed projects.",
    )
    permission_scheme_supported: PropertyRef = PropertyRef(
        "permission_scheme_supported",
        description="False for team-managed projects, whose scheme grants are not exported.",
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
        "id", description="Tenant-scoped stable resource identifier."
    )
    role_id: PropertyRef = PropertyRef(
        "role_id",
        description="Jira role ID; role assignments are scoped to the project.",
    )
    name: PropertyRef = PropertyRef("name", description="Role name.")
    description: PropertyRef = PropertyRef(
        "description", description="Role description."
    )
    admin: PropertyRef = PropertyRef(
        "admin", description="Whether Jira identifies this as the project admin role."
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
        "id", description="Tenant-scoped stable resource identifier."
    )
    grant_id: PropertyRef = PropertyRef(
        "grant_id", description="Permission grant ID within the scheme."
    )
    scheme_id: PropertyRef = PropertyRef(
        "scheme_id", description="Permission scheme ID."
    )
    permission: PropertyRef = PropertyRef(
        "permission",
        description="Permission key such as BROWSE_PROJECTS or ADMINISTER_PROJECTS.",
    )
    holder_type: PropertyRef = PropertyRef(
        "holder_type",
        description="Jira permission holder type, including conditional or app-specific holders.",
    )
    holder_parameter: PropertyRef = PropertyRef(
        "holder_parameter",
        description="Original holder parameter, such as group name or role ID.",
    )
    holder_value: PropertyRef = PropertyRef(
        "holder_value", description="Original stable holder value, such as group ID."
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

from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.nodes import ExtraNodeLabels
from cartography.models.notion.user import NotionWorkspaceToUserRel
from cartography.models.ontology.labels import USER_ACCOUNT


@dataclass(frozen=True)
class NotionSCIMUserNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "id",
        description="Workspace-scoped Notion user ID.",
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    notion_user_id: PropertyRef = PropertyRef(
        "notion_user_id",
        extra_index=True,
        description="Notion's user UUID.",
    )
    name: PropertyRef = PropertyRef("name", description="User display name.")
    email: PropertyRef = PropertyRef(
        "email",
        extra_index=True,
        description="User email when exposed to the connection.",
    )
    active: PropertyRef = PropertyRef(
        "active",
        description="Whether the SCIM account is active.",
    )
    workspace_role: PropertyRef = PropertyRef(
        "workspace_role",
        description="Notion workspace role returned by SCIM.",
    )
    scim_external_id: PropertyRef = PropertyRef(
        "scim_external_id",
        description="Identity provider ID supplied through SCIM.",
    )
    title: PropertyRef = PropertyRef("title", description="Job title.")
    user_type: PropertyRef = PropertyRef(
        "user_type",
        description="SCIM user type.",
    )
    locale: PropertyRef = PropertyRef("locale", description="SCIM locale.")
    preferred_language: PropertyRef = PropertyRef(
        "preferred_language",
        description="SCIM preferred language.",
    )
    department: PropertyRef = PropertyRef(
        "department",
        description="SCIM department.",
    )
    division: PropertyRef = PropertyRef("division", description="SCIM division.")
    cost_center: PropertyRef = PropertyRef(
        "cost_center",
        description="SCIM cost center.",
    )
    organization: PropertyRef = PropertyRef(
        "organization",
        description="SCIM organization.",
    )
    employee_number: PropertyRef = PropertyRef(
        "employee_number",
        description="SCIM employee number.",
    )
    manager_email: PropertyRef = PropertyRef(
        "manager_email",
        description="Manager email supplied by SCIM.",
    )
    is_workspace_member: PropertyRef = PropertyRef(
        "is_workspace_member",
        description="True only when SCIM confirms workspace membership.",
    )


@dataclass(frozen=True)
class NotionSCIMUserSchema(CartographyNodeSchema):
    """SCIM enrichment for a Notion user account."""

    label: str = "NotionUser"
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels([USER_ACCOUNT])
    properties: NotionSCIMUserNodeProperties = NotionSCIMUserNodeProperties()
    sub_resource_relationship: NotionWorkspaceToUserRel = NotionWorkspaceToUserRel()

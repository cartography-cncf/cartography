from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.nodes import ExtraNodeLabels
from cartography.models.ontology.labels import USER_ACCOUNT
from cartography.models.zendesk.tenant import ZendeskResourceToTenantRel


@dataclass(frozen=True)
class ZendeskUserNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "id", description="Tenant-scoped ID: subdomain:user_id."
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    user_id: PropertyRef = PropertyRef("user_id", description="Native Zendesk user ID.")
    name: PropertyRef = PropertyRef("name", description="User display name.")
    email: PropertyRef = PropertyRef(
        "email", extra_index=True, description="User email address."
    )
    role: PropertyRef = PropertyRef("role", description="Staff role: agent or admin.")
    role_type: PropertyRef = PropertyRef(
        "role_type", description="Zendesk agent role type, including light agents."
    )
    custom_role_id: PropertyRef = PropertyRef(
        "custom_role_id", description="Custom agent role ID, if assigned."
    )
    active: PropertyRef = PropertyRef(
        "active", description="Whether the user has not been deleted."
    )
    suspended: PropertyRef = PropertyRef(
        "suspended", description="Whether the user is suspended."
    )
    created_at: PropertyRef = PropertyRef(
        "created_at", description="Account creation time (ISO 8601)."
    )
    updated_at: PropertyRef = PropertyRef(
        "updated_at", description="Last modification time (ISO 8601)."
    )
    last_login_at: PropertyRef = PropertyRef(
        "last_login_at", description="Last login time (ISO 8601)."
    )


@dataclass(frozen=True)
class ZendeskUserSchema(CartographyNodeSchema):
    """A Zendesk CX agent or administrator, including light and suspended agents.

    End users are excluded. Ontology Mapping: This node has the extra label
    `UserAccount` to enable cross-platform queries for user accounts.

    Source API: [Zendesk List Users](https://developer.zendesk.com/api-reference/ticketing/users/users/#list-users),
    filtered to agent and admin roles.
    """

    label: str = "ZendeskUser"
    properties: ZendeskUserNodeProperties = ZendeskUserNodeProperties()
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels([USER_ACCOUNT])
    sub_resource_relationship: ZendeskResourceToTenantRel = ZendeskResourceToTenantRel()

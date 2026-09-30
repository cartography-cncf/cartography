from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.nodes import ExtraNodeLabels
from cartography.models.ontology.labels import TENANT


@dataclass(frozen=True)
class LangSmithOrganizationNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id", description="LangSmith organization UUID.")
    name: PropertyRef = PropertyRef(
        "display_name", description="Organization display name."
    )
    tier: PropertyRef = PropertyRef(
        "tier", description="Payment plan tier the organization is on."
    )
    disabled: PropertyRef = PropertyRef(
        "disabled", description="True if the organization is disabled."
    )
    is_personal: PropertyRef = PropertyRef(
        "is_personal",
        description="True if this is a personal organization rather than a shared one.",
    )
    sso_only: PropertyRef = PropertyRef(
        "sso_only",
        description="True if members may only authenticate through SSO.",
    )
    jit_provisioning_enabled: PropertyRef = PropertyRef(
        "jit_provisioning_enabled",
        description="True if SSO just-in-time user provisioning is enabled.",
    )
    invites_enabled: PropertyRef = PropertyRef(
        "invites_enabled",
        description="True if members may be invited to the organization.",
    )
    workspace_admin_can_invite_to_org: PropertyRef = PropertyRef(
        "workspace_admin_can_invite_to_org",
        description="True if workspace admins may invite users to the whole organization.",
    )
    pat_creation_disabled: PropertyRef = PropertyRef(
        "pat_creation_disabled",
        description="True if members are blocked from creating personal access tokens.",
    )
    public_sharing_disabled: PropertyRef = PropertyRef(
        "public_sharing_disabled",
        description="True if publicly sharing runs, prompts and datasets is blocked.",
    )
    max_api_key_expiry_days: PropertyRef = PropertyRef(
        "max_api_key_expiry_days",
        description="Maximum lifetime in days allowed for an API key, or null for unlimited.",
    )
    max_pat_expiry_days: PropertyRef = PropertyRef(
        "max_pat_expiry_days",
        description="Maximum lifetime in days allowed for a personal access token, or null for unlimited.",
    )
    max_service_key_expiry_days: PropertyRef = PropertyRef(
        "max_service_key_expiry_days",
        description="Maximum lifetime in days allowed for a service key, or null for unlimited.",
    )
    ip_allowlist_enabled: PropertyRef = PropertyRef(
        "ip_allowlist_enabled",
        description="True if an IP allowlist is enforced for this organization.",
    )
    sso_login_slug: PropertyRef = PropertyRef(
        "sso_login_slug", description="Vanity slug used for the SSO login URL."
    )
    security_contact: PropertyRef = PropertyRef(
        "security_contact",
        description="Email address listed as the organization's security contact.",
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class LangSmithOrganizationSchema(CartographyNodeSchema):
    """A LangSmith organization: the top-level tenant that owns workspaces, users and roles."""

    label: str = "LangSmithOrganization"
    properties: LangSmithOrganizationNodeProperties = (
        LangSmithOrganizationNodeProperties()
    )
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels([TENANT])

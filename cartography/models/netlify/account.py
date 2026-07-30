from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.nodes import ExtraNodeLabels
from cartography.models.ontology.labels import TENANT


# --- Node Definitions ---
@dataclass(frozen=True)
class NetlifyAccountNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    name: PropertyRef = PropertyRef("name", extra_index=True)
    slug: PropertyRef = PropertyRef("slug", extra_index=True)
    lifecycle_state: PropertyRef = PropertyRef("lifecycle_state")
    # Plan name and its billing identifiers. `type_name` is the human-readable plan
    # ("Free", "Pro", "Enterprise"); the ontology Tenant mapping does not use it but rules
    # that gate on plan-only features do.
    type_name: PropertyRef = PropertyRef("type_name")
    type_slug: PropertyRef = PropertyRef("type_slug")
    # Security posture of the team. `enforce_mfa` and `enforce_saml` are the enforcement
    # settings ("not_enforced" / "enforced"); `org_mfa_enabled` and `org_saml_enabled` report
    # whether the parent organization has turned the feature on at all.
    enforce_mfa: PropertyRef = PropertyRef("enforce_mfa")
    enforce_saml: PropertyRef = PropertyRef("enforce_saml")
    saml_enabled: PropertyRef = PropertyRef("saml_enabled")
    org_mfa_enabled: PropertyRef = PropertyRef("org_mfa_enabled")
    org_saml_enabled: PropertyRef = PropertyRef("org_saml_enabled")
    saml_session_expiration: PropertyRef = PropertyRef("saml_session_expiration")
    # Site-level access controls applied team-wide.
    site_access: PropertyRef = PropertyRef("site_access")
    site_sso_login: PropertyRef = PropertyRef("site_sso_login")
    site_sso_login_context: PropertyRef = PropertyRef("site_sso_login_context")
    has_site_password: PropertyRef = PropertyRef("has_site_password")
    site_password_context: PropertyRef = PropertyRef("site_password_context")
    # Any email domain listed here lets a matching user join the team without an invite.
    team_registration_domains: PropertyRef = PropertyRef("team_registration_domains")
    roles_allowed: PropertyRef = PropertyRef("roles_allowed")
    owner_ids: PropertyRef = PropertyRef("owner_ids")
    members_count: PropertyRef = PropertyRef("members_count")
    block_site_transfers: PropertyRef = PropertyRef("block_site_transfers")
    # Netlify support staff can be granted access to the team's resources.
    support_administration_enabled: PropertyRef = PropertyRef(
        "support_administration_enabled",
    )
    billing_email: PropertyRef = PropertyRef("billing_email")
    created_at: PropertyRef = PropertyRef("created_at")
    updated_at: PropertyRef = PropertyRef("updated_at")


# --- Main Schema ---
@dataclass(frozen=True)
class NetlifyAccountSchema(CartographyNodeSchema):
    """
    A Netlify team, the tenant that owns every other Netlify resource.
    """

    label: str = "NetlifyAccount"
    properties: NetlifyAccountNodeProperties = NetlifyAccountNodeProperties()
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels([TENANT])

from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.nodes import ExtraNodeLabels
from cartography.models.ontology.labels import TENANT


# --- Node Definitions ---
@dataclass(frozen=True)
class NetlifyAccountNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id", description="The Netlify team id.")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    name: PropertyRef = PropertyRef(
        "name", extra_index=True, description="Display name of the team."
    )
    slug: PropertyRef = PropertyRef(
        "slug",
        extra_index=True,
        description="URL slug of the team, used to address it in the API.",
    )
    lifecycle_state: PropertyRef = PropertyRef(
        "lifecycle_state", description="Team lifecycle state, e.g. `active`."
    )
    # Plan name and its billing identifiers. `type_name` is the human-readable plan
    # ("Free", "Pro", "Enterprise"); the ontology Tenant mapping does not use it but rules
    # that gate on plan-only features do.
    type_name: PropertyRef = PropertyRef(
        "type_name", description="Human-readable plan name, e.g. `Free`, `Pro`."
    )
    type_slug: PropertyRef = PropertyRef(
        "type_slug", description="Plan identifier, e.g. `credit-free`."
    )
    # Security posture of the team. `enforce_mfa` and `enforce_saml` are the enforcement
    # settings ("not_enforced" / "enforced"); `org_mfa_enabled` and `org_saml_enabled` report
    # whether the parent organization has turned the feature on at all.
    enforce_mfa: PropertyRef = PropertyRef(
        "enforce_mfa",
        description="Whether MFA is enforced for team members (`not_enforced` / `enforced`).",
    )
    enforce_saml: PropertyRef = PropertyRef(
        "enforce_saml",
        description="Whether SAML sign-in is enforced for team members.",
    )
    saml_enabled: PropertyRef = PropertyRef(
        "saml_enabled", description="Whether SAML is configured on this team."
    )
    org_mfa_enabled: PropertyRef = PropertyRef(
        "org_mfa_enabled",
        description="Whether the parent organization has MFA turned on.",
    )
    org_saml_enabled: PropertyRef = PropertyRef(
        "org_saml_enabled",
        description="Whether the parent organization has SAML turned on.",
    )
    saml_session_expiration: PropertyRef = PropertyRef(
        "saml_session_expiration", description="SAML session lifetime in seconds."
    )
    # Site-level access controls applied team-wide.
    site_access: PropertyRef = PropertyRef(
        "site_access",
        description="Default site access granted to members (`all`, `none`, ...).",
    )
    site_sso_login: PropertyRef = PropertyRef(
        "site_sso_login",
        description="Whether team SSO is required to view the team's sites.",
    )
    site_sso_login_context: PropertyRef = PropertyRef(
        "site_sso_login_context",
        description="Which deploy contexts the site SSO requirement applies to.",
    )
    has_site_password: PropertyRef = PropertyRef(
        "has_site_password",
        description="Whether a team-wide site password is set.",
    )
    site_password_context: PropertyRef = PropertyRef(
        "site_password_context",
        description="Which deploy contexts the site password applies to.",
    )
    # Any email domain listed here lets a matching user join the team without an invite.
    team_registration_domains: PropertyRef = PropertyRef(
        "team_registration_domains",
        description="Email domains whose users can join the team without an invite.",
    )
    roles_allowed: PropertyRef = PropertyRef(
        "roles_allowed", description="Member roles this plan permits."
    )
    owner_ids: PropertyRef = PropertyRef(
        "owner_ids", description="User ids of the team owners."
    )
    members_count: PropertyRef = PropertyRef(
        "members_count", description="Number of accepted members."
    )
    block_site_transfers: PropertyRef = PropertyRef(
        "block_site_transfers",
        description="Whether transferring sites out of the team is blocked.",
    )
    # Netlify support staff can be granted access to the team's resources.
    support_administration_enabled: PropertyRef = PropertyRef(
        "support_administration_enabled",
        description="Whether Netlify support staff may access the team's resources.",
    )
    billing_email: PropertyRef = PropertyRef(
        "billing_email", description="Billing contact address."
    )
    created_at: PropertyRef = PropertyRef(
        "created_at", description="When the team was created."
    )
    updated_at: PropertyRef = PropertyRef(
        "updated_at", description="When the team was last modified."
    )


# --- Main Schema ---
@dataclass(frozen=True)
class NetlifyAccountSchema(CartographyNodeSchema):
    """
    A Netlify team, the tenant that owns every other Netlify resource. Netlify has a single
    tenancy level: one Cartography run syncs one team, and every other node in this module is
    scoped to it.
    """

    label: str = "NetlifyAccount"
    properties: NetlifyAccountNodeProperties = NetlifyAccountNodeProperties()
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels([TENANT])

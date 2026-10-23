"""
Okta OAuth service app checks

An Okta OAuth service app (an API Services integration) calls the Okta
management API as itself, with no person or MFA in the loop. What it can do is
the intersection of its admin role, which limits the resources it can reach, and
its granted Okta API scopes, which limit the actions it can take.

These checks only evaluate orgs whose last sync could read app admin roles
(`OktaOrganization.application_roles_synced`), and, where they depend on scopes,
app scope grants (`OktaOrganization.app_grants_synced`), so data the credential
could not read is not mistaken for none.
"""

from cartography.rules.data.frameworks.iso27001 import iso27001_annex_a
from cartography.rules.data.frameworks.soc2 import soc2_tsc
from cartography.rules.spec.model import Fact
from cartography.rules.spec.model import Finding
from cartography.rules.spec.model import Maturity
from cartography.rules.spec.model import Module
from cartography.rules.spec.model import Rule
from cartography.rules.spec.model import RuleReference

_SERVICE_APP_REFERENCES = [
    RuleReference(
        text="Okta - Implement OAuth for Okta with a service app",
        url="https://developer.okta.com/docs/guides/implement-oauth-for-okta-serviceapp/main/",
    ),
    RuleReference(
        text="Okta - Standard administrator roles and permissions",
        url="https://help.okta.com/en-us/content/topics/security/administrators-admin-comparison.htm",
    ),
]

_DPOP_REFERENCES = [
    *_SERVICE_APP_REFERENCES,
    RuleReference(
        text="Okta - Configure OAuth 2.0 Demonstrating Proof-of-Possession",
        url="https://developer.okta.com/docs/guides/dpop/oktaresourceserver/main/",
    ),
]


class OktaPrivilegedServiceAppOutput(Finding):
    """Output model for Okta OAuth service apps that hold an admin role."""

    app_name: str | None = None
    app_id: str | None = None
    org_id: str | None = None
    role_types: list[str] | None = None
    write_scopes: list[str] | None = None
    token_endpoint_auth_method: str | None = None
    dpop_required: bool | None = None


# Active service apps holding at least one active admin role, one row per app.
_ACTIVE_ADMIN_SERVICE_APPS = """
    MATCH (o)-[:RESOURCE]->(app:OktaApplication)
    WHERE app.status = 'ACTIVE'
      AND app.settings_oauth_client_application_type = 'service'
    MATCH (app)-[:HAS_ROLE]->(role:OktaApplicationRole)
    WHERE role.status = 'ACTIVE'
    WITH o, app, collect(DISTINCT role.role_type) AS role_types
    WITH o, app, role_types,
        [scope IN coalesce(app.granted_scopes, []) WHERE scope CONTAINS '.manage']
            AS write_scopes
"""

_RETURN_SERVICE_APP = """
    RETURN
        app.label AS app_name,
        app.id AS app_id,
        o.id AS org_id,
        role_types,
        write_scopes,
        app.credentials_oauth_client_token_endpoint_auth_method
            AS token_endpoint_auth_method,
        app.settings_oauth_client_dpop_bound_access_tokens AS dpop_required
"""

_COUNT_SERVICE_APPS = """
    MATCH (o)-[:RESOURCE]->(app:OktaApplication)
    WHERE app.status = 'ACTIVE'
      AND app.settings_oauth_client_application_type = 'service'
    RETURN COUNT(app) AS count
"""


# =============================================================================
# Service apps that can change the org: an admin role and a `.manage` scope
# Main node: OktaApplication
# =============================================================================
_ORG_WITH_SYNCED_APP_PRIVILEGES = """
    MATCH (o:OktaOrganization)
    WHERE o.application_roles_synced = true AND o.app_grants_synced = true
"""

_SERVICE_APP_WITH_WRITE_ACCESS = (
    _ORG_WITH_SYNCED_APP_PRIVILEGES
    + _ACTIVE_ADMIN_SERVICE_APPS
    + """
    WHERE size(write_scopes) > 0
"""
)

okta_service_app_admin_write_access = Rule(
    id="okta_service_app_admin_write_access",
    name="Service App Can Change Okta",
    description=(
        "An Okta OAuth service app holds an admin role and at least one `.manage` "
        "Okta API scope, so whoever holds its key can create, change, or delete "
        "Okta resources within that role, with no person or MFA in the loop. Grant "
        "service apps only the read scopes they need, or the narrowest admin role "
        "that still allows their writes."
    ),
    output_model=OktaPrivilegedServiceAppOutput,
    facts=(
        Fact(
            id="okta_service_app_admin_role_with_manage_scope",
            name="Okta service apps with an admin role and a manage scope",
            description=(
                "Detects active Okta OAuth service apps that hold an active admin "
                "role and are granted at least one `.manage` Okta API scope. Only "
                "evaluates orgs whose app admin roles and scope grants were synced."
            ),
            cypher_query=_SERVICE_APP_WITH_WRITE_ACCESS + _RETURN_SERVICE_APP,
            cypher_visual_query=_SERVICE_APP_WITH_WRITE_ACCESS
            + """
    MATCH path=(app)-[:HAS_ROLE]->(:OktaApplicationRole)
    RETURN path
""",
            cypher_count_query=_ORG_WITH_SYNCED_APP_PRIVILEGES + _COUNT_SERVICE_APPS,
            asset_id_field="app_id",
            asset_label="OktaApplication",
            identity_fields=("app_id",),
            module=Module.OKTA,
            maturity=Maturity.EXPERIMENTAL,
        ),
    ),
    tags=(
        "iam",
        "non_human_identity",
        "privileged_access",
        "stride:elevation_of_privilege",
        "stride:tampering",
    ),
    version="0.1.0",
    references=_SERVICE_APP_REFERENCES,
    frameworks=(
        iso27001_annex_a("8.2"),
        soc2_tsc("CC6.3"),
    ),
)


# =============================================================================
# Admin service apps whose access tokens are not bound with DPoP
# Main node: OktaApplication
# =============================================================================
_ORG_WITH_SYNCED_APP_ROLES = """
    MATCH (o:OktaOrganization)
    WHERE o.application_roles_synced = true
"""

_ADMIN_SERVICE_APP_WITHOUT_DPOP = (
    _ORG_WITH_SYNCED_APP_ROLES
    + _ACTIVE_ADMIN_SERVICE_APPS
    + """
    WHERE coalesce(app.settings_oauth_client_dpop_bound_access_tokens, false) = false
"""
)

okta_admin_service_app_without_dpop = Rule(
    id="okta_admin_service_app_without_dpop",
    name="Admin Service App Without DPoP",
    description=(
        "An Okta OAuth service app holds an admin role but does not require "
        "Demonstrating Proof of Possession (DPoP). Its access tokens are then "
        "bearer tokens: anyone who steals one, for example from logs or a proxy, "
        "can call the Okta API with the app's admin role until the token expires. "
        "Require DPoP so each token only works with the app's own key."
    ),
    output_model=OktaPrivilegedServiceAppOutput,
    facts=(
        Fact(
            id="okta_admin_service_app_dpop_not_required",
            name="Okta admin service apps that do not require DPoP",
            description=(
                "Detects active Okta OAuth service apps that hold an active admin "
                "role and do not require DPoP-bound access tokens. Only evaluates "
                "orgs whose app admin roles were synced."
            ),
            cypher_query=_ADMIN_SERVICE_APP_WITHOUT_DPOP + _RETURN_SERVICE_APP,
            cypher_visual_query=_ADMIN_SERVICE_APP_WITHOUT_DPOP
            + """
    MATCH path=(app)-[:HAS_ROLE]->(:OktaApplicationRole)
    RETURN path
""",
            cypher_count_query=_ORG_WITH_SYNCED_APP_ROLES + _COUNT_SERVICE_APPS,
            asset_id_field="app_id",
            asset_label="OktaApplication",
            identity_fields=("app_id",),
            module=Module.OKTA,
            maturity=Maturity.EXPERIMENTAL,
        ),
    ),
    tags=(
        "iam",
        "credentials",
        "non_human_identity",
        "privileged_access",
        "stride:spoofing",
    ),
    version="0.1.0",
    references=_DPOP_REFERENCES,
    frameworks=(
        iso27001_annex_a("8.5"),
        soc2_tsc("CC6.1"),
    ),
)

from cartography.rules.data.frameworks.iso27001 import iso27001_annex_a
from cartography.rules.data.frameworks.soc2 import soc2_tsc
from cartography.rules.spec.model import Fact
from cartography.rules.spec.model import Finding
from cartography.rules.spec.model import Maturity
from cartography.rules.spec.model import Module
from cartography.rules.spec.model import Rule
from cartography.rules.spec.model import RuleReference

# Admin-only actions, such as managing users and API tokens, can't be granted
# to a custom role, so the built-in `admin` slug identifies full admin access.
_pylon_admin_service_account = Fact(
    id="pylon_admin_service_account",
    name="Active Pylon API tokens and bots with the Admin role",
    description=(
        "Detects active Pylon API token identities and bots that hold the "
        "built-in Admin role. Pylon tokens never expire and have no scopes, so "
        "anyone who obtains one of these tokens can manage users, delete "
        "customer records, and change workspace settings until it is revoked. "
        "Both token identities and bots appear as service accounts because "
        "they have no email address. A token acting as a user escapes detection "
        "because Pylon returns only the user's identity and email."
    ),
    cypher_query="""
    MATCH (org:PylonOrganization)-[:RESOURCE]->(sa:PylonServiceAccount)
    WHERE NOT coalesce(sa.is_deactivated, false)
      AND EXISTS { (sa)-[:HAS_ROLE]->(:PylonRole {slug: 'admin'}) }
    RETURN
        sa.name AS name,
        sa.id AS id,
        org.name AS organization,
        org.id AS organization_id
    """,
    cypher_visual_query="""
    MATCH p=(org:PylonOrganization)-[:RESOURCE]->(sa:PylonServiceAccount)-[:HAS_ROLE]->(role:PylonRole {slug: 'admin'})
    WHERE NOT coalesce(sa.is_deactivated, false)
    RETURN *
    """,
    cypher_count_query="""
    MATCH (sa:PylonServiceAccount)
    WHERE NOT coalesce(sa.is_deactivated, false)
    RETURN COUNT(sa) AS count
    """,
    asset_label="PylonServiceAccount",
    asset_id_field="id",
    identity_fields=("id",),
    module=Module.PYLON,
    maturity=Maturity.EXPERIMENTAL,
)


class PylonAdminServiceAccountOutput(Finding):
    name: str | None = None
    id: str | None = None
    organization: str | None = None
    organization_id: str | None = None


pylon_admin_service_accounts = Rule(
    id="pylon_admin_service_accounts",
    name="Pylon API Tokens and Bots With Admin Access",
    description=(
        "Pylon API tokens act with the full access of their role, never expire, "
        "and can't be scoped. Give each integration a bot or token identity "
        "with a custom or Viewer role that grants only what it needs, add an IP "
        "allowlist, and revoke unused Admin tokens."
    ),
    output_model=PylonAdminServiceAccountOutput,
    facts=(_pylon_admin_service_account,),
    tags=(
        "identity",
        "credentials",
        "pylon",
        "stride:elevation_of_privilege",
    ),
    version="0.1.0",
    references=[
        RuleReference(
            text="Pylon API authentication: roles and IP allowlists",
            url="https://docs.usepylon.com/pylon-docs/developer/api/authentication",
        ),
        RuleReference(
            text="Pylon roles and user management",
            url="https://docs.usepylon.com/pylon-docs/platform/roles-and-user-management",
        ),
    ],
    frameworks=(
        iso27001_annex_a("5.18"),
        iso27001_annex_a("8.2"),
        soc2_tsc("CC6.3"),
    ),
)

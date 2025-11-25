from cartography.rules.spec.model import Fact
from cartography.rules.spec.model import Finding
from cartography.rules.spec.model import Maturity
from cartography.rules.spec.model import Module
from cartography.rules.spec.model import Rule

# Facts
_inactive_user_active_accounts_ontology = Fact(
    id="inactive-user-active-accounts-ontology",
    name="Active Accounts Linked to Inactive User Identities",
    description=(
        "Finds user accounts (across integrated platforms) that are marked as active while their linked "
        "ontology User node is marked as inactive. Uses null-safe comparison to avoid false positives from "
        "missing data."
    ),
    # We use COALESCE to handle NULL value and default to the opposite of the expected value to avoid false positives with NULL comparison
    cypher_query="""
    MATCH (u:User)-[:HAS_ACCOUNT]-(a:UserAccount)
    WHERE COALESCE(u.active, True) = False
    AND COALESCE(a._ont_active, False) = True
    RETURN a.id AS account_id, a._ont_email AS account_email, u.id AS user_id, u.email AS user_email, a._ont_username AS account_username, u.fullname AS user_name, a._ont_source AS source
    """,
    cypher_visual_query="""
    MATCH (u:User)-[:HAS_ACCOUNT]-(a:UserAccount)
    WHERE COALESCE(u.active, True) = False
    AND COALESCE(a._ont_active, False) = True
    RETURN a, u
    """,
    module=Module.CROSS_CLOUD,
    maturity=Maturity.EXPERIMENTAL,
)


# Rule
class InactiveUserActiveAccountsOutput(Finding):
    account_username: str | None = None
    account_email: str | None = None
    user_name: str | None = None
    user_email: str | None = None
    account_id: str | None = None
    user_id: str | None = None


inactive_user_active_accounts = Rule(
    id="inactive-user-active-accounts",
    name="Active Accounts Linked to Inactive User Identities",
    description=(
        "Detects user accounts across cloud platforms and SaaS services that remain active despite being linked "
        "to inactive or terminated user identities in the source identity provider. This represents a critical "
        "identity lifecycle management gap that can lead to unauthorized access, privilege abuse, and compliance "
        "violations. When employees leave an organization or users are deactivated in identity providers (Okta, "
        "Azure AD, Google Workspace), their associated accounts in AWS, GCP, GitHub, and other services should be "
        "automatically deactivated or deleted. Active accounts linked to inactive identities may indicate incomplete "
        "offboarding procedures, broken identity provisioning workflows (SCIM failures), orphaned accounts created "
        "outside of SSO, or potential insider threats. Organizations should implement automated account lifecycle "
        "management, regular access reviews, and deprovisioning automation to ensure accounts are disabled when "
        "users become inactive."
    ),
    output_model=InactiveUserActiveAccountsOutput,
    tags=("identity", "iam", "compliance", "access_control"),
    facts=(_inactive_user_active_accounts_ontology,),
    version="0.2.0",
)

from cartography.rules.spec.model import Fact
from cartography.rules.spec.model import Finding
from cartography.rules.spec.model import Maturity
from cartography.rules.spec.model import Module
from cartography.rules.spec.model import Rule

# Facts
_inactive_user_active_accounts_ontology = Fact(
    id="inactive-user-active-accounts-ontology",
    name="Active accounts linked to inactive users",
    description="Finds user accounts that remain active despite being linked to inactive user identities.",
    # We use COALESCE to handle NULL value and default to the opposite of the expected value to avoid false positives with NULL comparison
    cypher_query="""
    MATCH (u:User)-[:HAS_ACCOUNT]-(a:UserAccount)
    WHERE COALESCE(u.active, True) = False
    AND COALESCE(a.active, False) = True
    RETURN a.id AS account_id, a._ont_email AS account_email, u.id AS user_id, u.email AS user_email, a._ont_username AS account_username, u.fullname AS user_name, a._ont_source AS source
    """,
    cypher_visual_query="""
    MATCH (u:User)-[:HAS_ACCOUNT]-(a:UserAccount)
    WHERE COALESCE(u.active, True) = False
    AND COALESCE(a.active, False) = True
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
    name="Active accounts linked to inactive users",
    description="Detects user accounts that remain active despite being linked to inactive user identities. When users are deactivated in the identity provider, their associated accounts should also be deactivated to prevent unauthorized access.",
    output_model=InactiveUserActiveAccountsOutput,
    tags=("identity", "iam", "compliance", "access_control"),
    facts=(_inactive_user_active_accounts_ontology,),
    version="0.1.0",
)

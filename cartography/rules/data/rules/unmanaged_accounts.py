from cartography.rules.spec.model import Fact
from cartography.rules.spec.model import Finding
from cartography.rules.spec.model import Maturity
from cartography.rules.spec.model import Module
from cartography.rules.spec.model import Rule

# Facts
_unmanaged_accounts_ontology = Fact(
    id="unmanaged-accounts-ontology",
    name="User accounts not linked to a user identity",
    description="Finds user accounts that are not linked to an ontology user node.",
    cypher_query="""
    MATCH (a:UserAccount)
    WHERE NOT (a)<-[:HAS_ACCOUNT]-(:User)
    return a.id as id, a.email AS email
    """,
    cypher_visual_query="""
    MATCH (a:UserAccount)
    WHERE NOT (a)<-[:HAS_ACCOUNT]-(:User)
    return a
    """,
    module=Module.CROSS_CLOUD,
    maturity=Maturity.EXPERIMENTAL,
)


# Rule
class UnmanagedAccountRuleOutput(Finding):
    id: str | None = None
    email: str | None = None


unmanaged_accounts = Rule(
    id="unmanaged-account",
    name="User accounts not linked to a user identity",
    description="Detects user accounts that do not have Multi-Factor Authentication enabled.",
    output_model=UnmanagedAccountRuleOutput,
    tags=("identity", "iam", "compliance"),
    facts=(_unmanaged_accounts_ontology,),
    version="0.1.0",
)

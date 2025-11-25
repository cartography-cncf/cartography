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
    AND (a.active = true OR a.active IS NULL)
    return a.id as id, a._ont_email AS email, a._ont_source AS source
    """,
    cypher_visual_query="""
    MATCH (a:UserAccount)
    WHERE NOT (a)<-[:HAS_ACCOUNT]-(:User)
    AND (a.active = true OR a.active IS NULL)
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
    description="Detects accounts that are not linked to a known user identity (inactive accounts are excluded).",
    output_model=UnmanagedAccountRuleOutput,
    tags=("identity", "iam", "compliance"),
    facts=(_unmanaged_accounts_ontology,),
    version="0.1.1",
)

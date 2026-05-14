from cartography.rules.data.frameworks.iso27001 import iso27001_annex_a
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
    AND COALESCE(a._ont_active, true)
    AND NOT COALESCE(a._ont_inactive, false)
    AND COALESCE(a.active, true)
    AND NOT (a:KubernetesUser AND (a.name STARTS WITH 'eks:' OR a.name STARTS WITH 'system:'))
    AND NOT (a:SlackUser AND a.id = 'USLACKBOT')
    return a.id as id, a._ont_email AS email, a._ont_source AS source
    """,
    cypher_visual_query="""
    MATCH (a:UserAccount)
    WHERE NOT (a)<-[:HAS_ACCOUNT]-(:User)
    AND COALESCE(a._ont_active, true)
    AND NOT COALESCE(a._ont_inactive, false)
    AND COALESCE(a.active, true)
    AND NOT (a:KubernetesUser AND (a.name STARTS WITH 'eks:' OR a.name STARTS WITH 'system:'))
    AND NOT (a:SlackUser AND a.id = 'USLACKBOT')
    return a
    """,
    cypher_count_query="""
    MATCH (a:UserAccount)
    WHERE COALESCE(a._ont_active, true)
    AND NOT COALESCE(a._ont_inactive, false)
    AND COALESCE(a.active, true)
    AND NOT (a:KubernetesUser AND (a.name STARTS WITH 'eks:' OR a.name STARTS WITH 'system:'))
    AND NOT (a:SlackUser AND a.id = 'USLACKBOT')
    RETURN COUNT(a) AS count
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
    frameworks=(
        iso27001_annex_a("5.16"),
        iso27001_annex_a("5.18"),
    ),
)

from cartography.rules.spec.model import Fact
from cartography.rules.spec.model import Finding
from cartography.rules.spec.model import FindingOutput
from cartography.rules.spec.model import Module

# Facts
_unmanaged_account_ontology = Fact(
    id="unmanaged-account-ontology",
    name="User accounts not linked to a user identity",
    description="Finds user accounts that are not linked to an ontology user node.",
    module=Module.CROSS_CLOUD,
    cypher_query="""
    MATCH (a:UserAccount)
    WHERE NOT (a)<-[:HAS_ACCOUNT]-(:User)
    return a.id as id, a.email AS email, a._module_name AS _source
    """,
    cypher_visual_query="""
    MATCH (a:UserAccount)
    WHERE NOT (a)<-[:HAS_ACCOUNT]-(:User)
    return a
    """,
)


# Finding
class UnmanagedAccountFindingOutput(FindingOutput):
    id: str | None = None
    email: str | None = None


unmanaged_account = Finding(
    id="unmanaged-account",
    name="User accounts not linked to a user identity",
    description="Detects user accounts that do not have Multi-Factor Authentication enabled.",
    tags=("identity",),
    facts=(_unmanaged_account_ontology,),
    output_model=UnmanagedAccountFindingOutput,
)

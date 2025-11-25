from cartography.rules.spec.model import Fact
from cartography.rules.spec.model import Finding
from cartography.rules.spec.model import Maturity
from cartography.rules.spec.model import Module
from cartography.rules.spec.model import Rule

# Facts
_unmanaged_accounts_ontology = Fact(
    id="unmanaged-accounts-ontology",
    name="Active Accounts Without User Identity Links",
    description=(
        "Finds UserAccount nodes that do not have an incoming HAS_ACCOUNT relationship from any User node and are "
        "either marked as active or have null active status (to avoid missing accounts where status is not tracked)."
    ),
    cypher_query="""
    MATCH (a:UserAccount)
    WHERE NOT (a)<-[:HAS_ACCOUNT]-(:User)
    AND (a._ont_active = true OR a._ont_active IS NULL)
    return a.id as id, a._ont_email AS email, a._ont_source AS source
    """,
    cypher_visual_query="""
    MATCH (a:UserAccount)
    WHERE NOT (a)<-[:HAS_ACCOUNT]-(:User)
    AND (a._ont_active = true OR a._ont_active IS NULL)
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
    name="Active Accounts Without Linked User Identities",
    description=(
        "Detects active user accounts across cloud platforms and services that are not linked to a known user "
        "identity in the central identity ontology. These orphaned or unmanaged accounts represent identity "
        "governance gaps and potential security risks because they exist outside of normal identity lifecycle "
        "management, deprovisioning workflows, and access control policies. Unmanaged accounts may result from "
        "manual account creation outside of SSO/identity provider flows, legacy accounts created before identity "
        "federation was implemented, service accounts or bot accounts that were not properly classified, shadow "
        "IT where users created accounts without IT approval, or failed/incomplete account deletion processes. "
        "These accounts are concerning because they bypass centralized authentication policies (no MFA enforcement, "
        "no password policies), don't appear in access reviews or recertification processes, won't be disabled when "
        "users leave the organization, and represent potential persistence mechanisms for attackers. Organizations "
        "should implement comprehensive provisioning to ensure all accounts are linked to identity sources, conduct "
        "regular discovery and remediation of orphaned accounts, classify legitimate service accounts properly, and "
        "monitor for new account creation outside of approved provisioning workflows."
    ),
    output_model=UnmanagedAccountRuleOutput,
    tags=("identity", "iam", "compliance", "governance"),
    facts=(_unmanaged_accounts_ontology,),
    version="0.2.0",
)

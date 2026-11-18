from cartography.graph.analysis import AnalysisJob
from cartography.graph.analysis import AnalysisStatement
from cartography.graph.analysis import Param
from cartography.graph.analysis import ScopeById
from cartography.graph.analysis import SetProperties
from cartography.graph.analysis import Var


# GitHub scopes these facts to the organization being synced, and a user can belong
# to several organizations. Each MEMBER_OF and UNAFFILIATED relationship holds its
# organization's answer, and the GitHubUser node holds the combination. max() skips
# nulls and ranks true above false, so an organization that reports 2FA or enterprise
# ownership outranks one that denies it or cannot see it.
def _organization_facts(memberships: str) -> AnalysisStatement:
    return AnalysisStatement(
        match=f"""
        {memberships}
        WITH user,
            max(membership.has_2fa_enabled) AS has_2fa_enabled,
            coalesce(max(membership.is_enterprise_owner), false) AS is_enterprise_owner,
            collect(membership.organization_verified_domain_emails) AS verified_email_lists,
            collect(membership.normalized_emails) AS normalized_email_lists
        WITH user, has_2fa_enabled, is_enterprise_owner,
            COLLECT {{
                UNWIND verified_email_lists AS emails UNWIND emails AS email
                RETURN DISTINCT email ORDER BY email
            }} AS organization_verified_domain_emails,
            COLLECT {{
                UNWIND normalized_email_lists AS emails UNWIND emails AS email
                RETURN DISTINCT email ORDER BY email
            }} AS normalized_emails
        """,
        effects=(
            SetProperties(
                "user",
                {
                    "has_2fa_enabled": Var("has_2fa_enabled"),
                    "_ont_has_mfa": Var("has_2fa_enabled"),
                    "is_enterprise_owner": Var("is_enterprise_owner"),
                    "organization_verified_domain_emails": Var(
                        "organization_verified_domain_emails"
                    ),
                    "normalized_emails": Var("normalized_emails"),
                    "organization_facts_lastupdated": Param("UPDATE_TAG"),
                },
                label="GitHubUser",
                cleanup_stamp="organization_facts_lastupdated",
            ),
        ),
    )


# Runs in each organization's user sync, so the values are right after that sync
# alone: an orchestrator can sync organizations separately and skip the step that
# follows all of them. Users are not a RESOURCE of the organization, so the generated
# cleanup reaches no user and the job only replaces values. A reader or a concurrent
# organization sync never sees them missing.
GITHUB_ORGANIZATION_USER_FACTS = AnalysisJob(
    name="GitHub user organization facts for one organization",
    short_name="github_organization_user_facts",
    scope=ScopeById("GitHubOrganization", "ORG_URL", scope_on="org"),
    statements=(
        # A user who changes between member and unaffiliated keeps the old
        # relationship to this organization until the global cleanup runs, so
        # only the user's freshest relationship to it counts.
        _organization_facts(
            """
            MATCH (org:GitHubOrganization)<-[current:MEMBER_OF|UNAFFILIATED]-(user:GitHubUser)
            WITH org, user, max(current.lastupdated) AS refreshed
            MATCH (user)-[membership:MEMBER_OF|UNAFFILIATED]->(member_of:GitHubOrganization)
            WHERE member_of <> org OR membership.lastupdated = refreshed
            """
        ),
    ),
)
# Runs after stale memberships are deleted. The user cleanup keeps the nodes of users
# left without a membership, so the generated cleanup clears their facts.
GITHUB_USER_ORGANIZATION_FACTS = AnalysisJob(
    name="GitHub user organization facts",
    short_name="github_user_organization_facts",
    statements=(
        _organization_facts(
            "MATCH (user:GitHubUser)-[membership:MEMBER_OF|UNAFFILIATED]->(:GitHubOrganization)"
        ),
    ),
)

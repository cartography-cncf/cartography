from cartography.rules.data.frameworks.iso27001 import iso27001_annex_a
from cartography.rules.spec.model import Fact
from cartography.rules.spec.model import Finding
from cartography.rules.spec.model import Maturity
from cartography.rules.spec.model import Module
from cartography.rules.spec.model import Rule
from cartography.rules.spec.model import RuleReference

_github_public_pull_request_target_write_token = Fact(
    id="github_public_pull_request_target_write_token",
    name="Public GitHub workflows using pull_request_target with write token scopes",
    description=(
        "Public repositories whose GitHub Actions workflows run on "
        "pull_request_target and explicitly request write-capable GITHUB_TOKEN "
        "permissions."
    ),
    cypher_query="""
    MATCH (repo:GitHubRepository)-[:HAS_WORKFLOW]->(workflow:GitHubWorkflow)
    WHERE coalesce(repo.private, false) = false
      AND coalesce(repo.archived, false) = false
      AND 'pull_request_target' IN coalesce(workflow.trigger_events, [])
    WITH repo, workflow,
         [scope IN [
             CASE WHEN workflow.permissions_actions = 'write' THEN 'actions' ELSE null END,
             CASE WHEN workflow.permissions_contents = 'write' THEN 'contents' ELSE null END,
             CASE WHEN workflow.permissions_packages = 'write' THEN 'packages' ELSE null END,
             CASE WHEN workflow.permissions_pull_requests = 'write' THEN 'pull_requests' ELSE null END,
             CASE WHEN workflow.permissions_issues = 'write' THEN 'issues' ELSE null END,
             CASE WHEN workflow.permissions_deployments = 'write' THEN 'deployments' ELSE null END,
             CASE WHEN workflow.permissions_statuses = 'write' THEN 'statuses' ELSE null END,
             CASE WHEN workflow.permissions_checks = 'write' THEN 'checks' ELSE null END,
             CASE WHEN workflow.permissions_id_token = 'write' THEN 'id_token' ELSE null END,
             CASE WHEN workflow.permissions_security_events = 'write' THEN 'security_events' ELSE null END
         ] WHERE scope IS NOT NULL] AS write_scopes
    WHERE size(write_scopes) > 0
    RETURN
        repo.id AS repo_id,
        repo.fullname AS repo,
        repo.defaultbranch AS default_branch,
        workflow.id AS workflow_id,
        workflow.name AS workflow_name,
        workflow.path AS workflow_path,
        workflow.trigger_events AS trigger_events,
        write_scopes
    ORDER BY repo, workflow_path
    """,
    cypher_visual_query="""
    MATCH p=(repo:GitHubRepository)-[:HAS_WORKFLOW]->(workflow:GitHubWorkflow)
    WHERE coalesce(repo.private, false) = false
      AND coalesce(repo.archived, false) = false
      AND 'pull_request_target' IN coalesce(workflow.trigger_events, [])
      AND (
          workflow.permissions_actions = 'write'
          OR workflow.permissions_contents = 'write'
          OR workflow.permissions_packages = 'write'
          OR workflow.permissions_pull_requests = 'write'
          OR workflow.permissions_issues = 'write'
          OR workflow.permissions_deployments = 'write'
          OR workflow.permissions_statuses = 'write'
          OR workflow.permissions_checks = 'write'
          OR workflow.permissions_id_token = 'write'
          OR workflow.permissions_security_events = 'write'
      )
    RETURN *
    """,
    cypher_count_query="""
    MATCH (repo:GitHubRepository)-[:HAS_WORKFLOW]->(workflow:GitHubWorkflow)
    WHERE coalesce(repo.private, false) = false
      AND coalesce(repo.archived, false) = false
      AND 'pull_request_target' IN coalesce(workflow.trigger_events, [])
    RETURN COUNT(workflow) AS count
    """,
    asset_id_field="workflow_id",
    module=Module.GITHUB,
    maturity=Maturity.EXPERIMENTAL,
)


class GitHubActionsPrivilegedPullRequest(Finding):
    repo_id: str | None = None
    repo: str | None = None
    default_branch: str | None = None
    workflow_id: str | None = None
    workflow_name: str | None = None
    workflow_path: str | None = None
    trigger_events: list[str] | None = None
    write_scopes: list[str] | None = None


github_actions_privileged_pull_request = Rule(
    id="github_actions_privileged_pull_request",
    name="GitHub Actions pull_request_target With Write Token",
    description=(
        "Public repositories with pull_request_target workflows that request "
        "write-capable token scopes. This is a supply-chain trust boundary: "
        "untrusted pull request content can influence a workflow running in "
        "the base repository security context if the workflow is unsafe."
    ),
    output_model=GitHubActionsPrivilegedPullRequest,
    facts=(_github_public_pull_request_target_write_token,),
    tags=(
        "supply_chain",
        "github",
        "ci_cd",
        "stride:tampering",
        "stride:elevation_of_privilege",
    ),
    version="0.1.0",
    references=[
        RuleReference(
            text="GitHub - Security hardening for GitHub Actions",
            url="https://docs.github.com/en/actions/security-for-github-actions/security-guides/security-hardening-for-github-actions",
        ),
        RuleReference(
            text="GitHub - Automatic token authentication",
            url="https://docs.github.com/en/actions/security-for-github-actions/security-guides/automatic-token-authentication",
        ),
    ],
    frameworks=(
        iso27001_annex_a("8.25"),
        iso27001_annex_a("8.28"),
        iso27001_annex_a("8.32"),
    ),
)

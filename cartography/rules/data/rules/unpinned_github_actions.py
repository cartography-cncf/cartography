from cartography.rules.spec.model import Fact
from cartography.rules.spec.model import Finding
from cartography.rules.spec.model import Maturity
from cartography.rules.spec.model import Module
from cartography.rules.spec.model import Rule
from cartography.rules.spec.model import RuleReference

_unpinned_github_actions_fact = Fact(
    id="unpinned-github-actions",
    name="GitHub workflows using unpinned third-party Actions",
    description=(
        "Finds GitHub Actions referenced by workflows that are not pinned to a full "
        "commit SHA. Local (./.github/actions/...) and docker:// references are excluded."
    ),
    cypher_query="""
    MATCH (repo:GitHubRepository)-[:HAS_WORKFLOW]->(wf:GitHubWorkflow)-[:USES_ACTION]->(a:GitHubAction)
    WHERE a.is_pinned = false
      AND a.is_local = false
      AND a.owner <> 'docker'
    RETURN
        a.full_name AS action,
        a.version AS version,
        wf.path AS workflow_path,
        repo.fullname AS repo,
        a.id AS action_id
    ORDER BY repo, workflow_path, action
    """,
    cypher_visual_query="""
    MATCH (repo:GitHubRepository)-[:HAS_WORKFLOW]->(wf:GitHubWorkflow)-[:USES_ACTION]->(a:GitHubAction)
    WHERE a.is_pinned = false
      AND a.is_local = false
      AND a.owner <> 'docker'
    RETURN *
    """,
    cypher_count_query="""
    MATCH (a:GitHubAction)
    WHERE a.is_local = false
      AND a.owner <> 'docker'
    RETURN COUNT(a) AS count
    """,
    asset_id_field="action_id",
    module=Module.GITHUB,
    maturity=Maturity.EXPERIMENTAL,
)


class UnpinnedGitHubActionOutput(Finding):
    action: str | None = None
    version: str | None = None
    workflow_path: str | None = None
    repo: str | None = None
    action_id: str | None = None


unpinned_github_actions = Rule(
    id="unpinned-github-actions",
    name="Unpinned GitHub Actions",
    description=(
        "Detects workflows referencing third-party GitHub Actions by a mutable ref "
        "(branch or tag) instead of a full commit SHA. If the upstream action is "
        "compromised — as with tj-actions/changed-files in March 2025 — attackers "
        "can retarget a tag at malicious code that then runs with the workflow's "
        "secrets. Pin to a full SHA and let Dependabot keep the pin current."
    ),
    output_model=UnpinnedGitHubActionOutput,
    tags=("supply_chain", "github", "stride:tampering"),
    facts=(_unpinned_github_actions_fact,),
    version="0.1.0",
    references=[
        RuleReference(
            text="GitHub - Security hardening for GitHub Actions (pin to full-length commit SHA)",
            url="https://docs.github.com/en/actions/security-for-github-actions/security-guides/security-hardening-for-github-actions#using-third-party-actions",
        ),
        RuleReference(
            text="CISA - Supply Chain Compromise of Third-Party tj-actions/changed-files (CVE-2025-30066)",
            url="https://www.cisa.gov/news-events/alerts/2025/03/18/supply-chain-compromise-third-party-tj-actionschanged-files-cve-2025-30066",
        ),
        RuleReference(
            text="StepSecurity - Harden-Runner detection of tj-actions/changed-files compromise",
            url="https://www.stepsecurity.io/blog/harden-runner-detection-tj-actions-changed-files-action-is-compromised",
        ),
    ],
)

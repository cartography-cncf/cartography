from cartography.rules.spec.model import Fact
from cartography.rules.spec.model import Finding
from cartography.rules.spec.model import Maturity
from cartography.rules.spec.model import Module
from cartography.rules.spec.model import Rule
from cartography.rules.spec.model import RuleReference

# Filter applied consistently across query, visual query, and count query:
# - is_pinned: false          -> action not pinned to a full commit SHA
# - is_local: false           -> exclude in-repo actions (./.github/actions/...)
# - owner <> 'docker'         -> exclude docker:// references (different pinning model)
_UNPINNED_ACTION_MATCH = """
MATCH (repo:GitHubRepository)-[:HAS_WORKFLOW]->(wf:GitHubWorkflow)-[:USES_ACTION]->(a:GitHubAction)
WHERE a.is_pinned = false
  AND a.is_local = false
  AND a.owner <> 'docker'
"""

_TOTAL_ACTIONS_MATCH = """
MATCH (a:GitHubAction)
WHERE a.is_local = false
  AND a.owner <> 'docker'
"""


_unpinned_github_actions_fact = Fact(
    id="unpinned-github-actions",
    name="GitHub workflows using unpinned third-party Actions",
    description=(
        "Finds GitHub Actions referenced by workflows that are not pinned to a full "
        "commit SHA. Mutable references (branches, tags, major-version tags) let a "
        "compromised upstream maintainer swap in malicious code on the next workflow "
        "run. Local actions (./.github/actions/...) and docker:// references are "
        "excluded."
    ),
    cypher_query=_UNPINNED_ACTION_MATCH
    + """
    RETURN
        a.full_name AS action,
        a.version AS version,
        wf.path AS workflow_path,
        repo.fullname AS repo,
        a.id AS action_id
    ORDER BY repo, workflow_path, action
    """,
    cypher_visual_query=_UNPINNED_ACTION_MATCH
    + """
    RETURN *
    """,
    cypher_count_query=_TOTAL_ACTIONS_MATCH
    + """
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
        "Detects GitHub workflows that reference third-party GitHub Actions using a "
        "mutable reference (branch or tag) rather than a full commit SHA. A "
        "compromise of the upstream action repository — as happened with "
        "tj-actions/changed-files in March 2025 — lets attackers retarget an "
        "existing tag at malicious code, which then executes with the workflow's "
        "permissions and access to its secrets on the next run. Pinning every "
        "third-party action to a full 40-character commit SHA, combined with "
        "Dependabot to keep those pins current, is the mitigation recommended by "
        "GitHub's security hardening guide."
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

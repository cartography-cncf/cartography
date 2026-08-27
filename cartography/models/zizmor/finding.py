from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.nodes import ExtraNodeLabels
from cartography.models.core.relationships import CartographyRelProperties
from cartography.models.core.relationships import CartographyRelSchema
from cartography.models.core.relationships import LinkDirection
from cartography.models.core.relationships import make_target_node_matcher
from cartography.models.core.relationships import OtherRelationships
from cartography.models.core.relationships import TargetNodeMatcher
from cartography.models.ontology.labels import SECURITY_ISSUE


@dataclass(frozen=True)
class ZizmorFindingNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "id",
        description=(
            "Synthetic finding identifier. Zizmor does not emit a stable finding ID, "
            "so this is a hash of the audit, repository, workflow path, and YAML route."
        ),
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    audit_id: PropertyRef = PropertyRef(
        "audit_id",
        extra_index=True,
        description=(
            "Identifier of the zizmor audit that produced the finding, "
            "such as `template-injection` or `unpinned-uses`."
        ),
    )
    description: PropertyRef = PropertyRef(
        "description",
        description="Short description of the weakness reported by the audit.",
    )
    url: PropertyRef = PropertyRef(
        "url",
        description="Link to the zizmor documentation page for this audit.",
    )
    severity: PropertyRef = PropertyRef(
        "severity",
        extra_index=True,
        description=(
            "Severity determined by zizmor: `informational`, `low`, `medium`, or `high`."
        ),
    )
    confidence: PropertyRef = PropertyRef(
        "confidence",
        description="Confidence determined by zizmor: `low`, `medium`, or `high`.",
    )
    persona: PropertyRef = PropertyRef(
        "persona",
        description=(
            "Persona the finding is reported for: `regular`, `pedantic`, or `auditor`."
        ),
    )
    ignored: PropertyRef = PropertyRef(
        "ignored",
        description=(
            "Whether the finding was suppressed by a `# zizmor: ignore[...]` comment. "
            "Only true when the report was produced with `--no-ignores`, since zizmor "
            "otherwise omits suppressed findings entirely. Rules disabled through "
            "zizmor's configuration file are reported like any other finding."
        ),
    )
    repository: PropertyRef = PropertyRef(
        "repositoryName",
        extra_index=True,
        description="Repository the finding was discovered in, in `owner/repo` form.",
    )
    repository_url: PropertyRef = PropertyRef(
        "repositoryUrl",
        extra_index=True,
        description="Full URL of the repository the finding was discovered in.",
    )
    branch: PropertyRef = PropertyRef(
        "branch",
        description="Repository branch the scanned workflow files were read from.",
    )
    file_path: PropertyRef = PropertyRef(
        "file_path",
        extra_index=True,
        description="Repository-relative path of the audited workflow or action file.",
    )
    yaml_route: PropertyRef = PropertyRef(
        "yaml_route",
        description=(
            "Dotted YAML path of the offending node, such as `jobs.greet.steps.0.run`."
        ),
    )
    uses_reference: PropertyRef = PropertyRef(
        "uses_reference",
        extra_index=True,
        description=(
            "Raw `uses` reference the finding points at, when the finding concerns a "
            "step or job that calls an action. Null for other findings."
        ),
    )
    annotation: PropertyRef = PropertyRef(
        "annotation",
        description="Zizmor's explanation of why the primary location is a problem.",
    )
    snippet: PropertyRef = PropertyRef(
        "snippet",
        description="Source excerpt of the primary location.",
    )
    start_line: PropertyRef = PropertyRef(
        "start_line",
        description="One-based line where the primary location starts.",
    )
    start_col: PropertyRef = PropertyRef(
        "start_col",
        description="One-based column where the primary location starts.",
    )
    end_line: PropertyRef = PropertyRef(
        "end_line",
        description="One-based line where the primary location ends.",
    )
    end_col: PropertyRef = PropertyRef(
        "end_col",
        description="One-based column where the primary location ends.",
    )
    fix_titles: PropertyRef = PropertyRef(
        "fix_titles",
        description="Titles of the fixes zizmor can apply for this finding.",
    )
    fix_dispositions: PropertyRef = PropertyRef(
        "fix_dispositions",
        description=(
            "Disposition of each available fix, `safe` or `unsafe`, in the same order "
            "as `fix_titles`."
        ),
    )


@dataclass(frozen=True)
class ZizmorFindingToGitHubWorkflowRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:ZizmorFinding)-[:AFFECTS]->(:GitHubWorkflow)
class ZizmorFindingToGitHubWorkflowRel(CartographyRelSchema):
    """Links a zizmor finding to the GitHub Actions workflow it was found in."""

    target_node_label: str = "GitHubWorkflow"
    # A workflow is uniquely identified by its repository plus its repo-relative path.
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {
            "repo_url": PropertyRef("repositoryUrl"),
            "path": PropertyRef("file_path"),
        },
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "AFFECTS"
    properties: ZizmorFindingToGitHubWorkflowRelProperties = (
        ZizmorFindingToGitHubWorkflowRelProperties()
    )


@dataclass(frozen=True)
class ZizmorFindingToGitHubActionRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:ZizmorFinding)-[:AFFECTS]->(:GitHubAction)
class ZizmorFindingToGitHubActionRel(CartographyRelSchema):
    """
    Links a zizmor finding to the action it concerns.

    Only findings whose location is a `uses` key resolve to an action, so this
    relationship is absent for findings reported against a `run` block, a job's
    permissions, or a workflow trigger.
    """

    target_node_label: str = "GitHubAction"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("action_id")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "AFFECTS"
    properties: ZizmorFindingToGitHubActionRelProperties = (
        ZizmorFindingToGitHubActionRelProperties()
    )


@dataclass(frozen=True)
class ZizmorFindingToGitHubRepoRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:ZizmorFinding)-[:FOUND_IN]->(:GitHubRepository)
class ZizmorFindingToGitHubRepoRel(CartographyRelSchema):
    """Links a zizmor finding to the GitHub repository containing the audited file."""

    target_node_label: str = "GitHubRepository"
    # GitHubRepository.id stores the repository URL, so repositoryUrl is the join key.
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("repositoryUrl")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "FOUND_IN"
    properties: ZizmorFindingToGitHubRepoRelProperties = (
        ZizmorFindingToGitHubRepoRelProperties()
    )


@dataclass(frozen=True)
class ZizmorFindingSchema(CartographyNodeSchema):
    """
    A CI supply-chain weakness reported by zizmor against a GitHub Actions file.

    Zizmor reports are ingested from files rather than by running the binary, so
    there is no tenant-like node to scope cleanup to. Stale findings are instead
    removed per repository by the module's cleanup function.
    """

    label: str = "ZizmorFinding"
    scoped_cleanup: bool = False
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels([SECURITY_ISSUE])
    properties: ZizmorFindingNodeProperties = ZizmorFindingNodeProperties()
    other_relationships: OtherRelationships = OtherRelationships(
        [
            ZizmorFindingToGitHubWorkflowRel(),
            ZizmorFindingToGitHubActionRel(),
            ZizmorFindingToGitHubRepoRel(),
        ],
    )

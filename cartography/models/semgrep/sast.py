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


@dataclass(frozen=True)
class SemgrepSASTFindingNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "id",
        description="Unique finding identifier from Semgrep Cloud or synthesized for an OSS finding.",
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    rule_id: PropertyRef = PropertyRef(
        "ruleId",
        extra_index=True,
        description="Identifier of the rule that triggered the finding.",
    )
    repository: PropertyRef = PropertyRef(
        "repositoryName",
        extra_index=True,
        description="Repository path where the finding was discovered.",
    )
    repository_url: PropertyRef = PropertyRef(
        "repositoryUrl",
        description="Full URL of the repository where the finding was discovered.",
    )
    branch: PropertyRef = PropertyRef(
        "branch",
        description="Repository branch where the finding was discovered.",
    )
    title: PropertyRef = PropertyRef(
        "title",
        extra_index=True,
        description="Short title for the finding.",
    )
    description: PropertyRef = PropertyRef(
        "description",
        description="Description of the vulnerability from the rule message.",
    )
    severity: PropertyRef = PropertyRef(
        "severity",
        description="Severity assigned to the finding.",
    )
    confidence: PropertyRef = PropertyRef(
        "confidence",
        description="Confidence assigned to the finding.",
    )
    categories: PropertyRef = PropertyRef(
        "categories",
        description="Categories associated with the finding.",
    )
    cwe_names: PropertyRef = PropertyRef(
        "cweNames",
        description="CWE identifiers associated with the rule.",
    )
    owasp_names: PropertyRef = PropertyRef(
        "owaspNames",
        description="OWASP category names associated with the rule.",
    )
    file_path: PropertyRef = PropertyRef(
        "filePath",
        extra_index=True,
        description="Path of the file where the finding was discovered.",
    )
    start_line: PropertyRef = PropertyRef(
        "startLine",
        description="Line where the finding starts.",
    )
    start_col: PropertyRef = PropertyRef(
        "startCol",
        description="Column where the finding starts.",
    )
    end_line: PropertyRef = PropertyRef(
        "endLine",
        description="Line where the finding ends.",
    )
    end_col: PropertyRef = PropertyRef(
        "endCol",
        description="Column where the finding ends.",
    )
    line_of_code_url: PropertyRef = PropertyRef(
        "lineOfCodeUrl",
        description="URL of the affected line of code. Available for cloud findings.",
    )
    state: PropertyRef = PropertyRef(
        "state",
        description="Current cloud finding state.",
    )
    fix_status: PropertyRef = PropertyRef(
        "fixStatus",
        description="Cloud finding fix status based on triage.",
    )
    triage_status: PropertyRef = PropertyRef(
        "triageStatus",
        description="Cloud finding triage status.",
    )
    opened_at: PropertyRef = PropertyRef(
        "openedAt",
        description="UTC date and time when the cloud finding was opened.",
    )


@dataclass(frozen=True)
class SemgrepSASTFindingToSemgrepDeploymentRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:SemgrepSASTFinding)<-[:RESOURCE]-(:SemgrepDeployment)
class SemgrepSASTFindingToSemgrepDeploymentRel(CartographyRelSchema):
    """Connects a Semgrep deployment to one of its SAST findings."""

    target_node_label: str = "SemgrepDeployment"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("DEPLOYMENT_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: SemgrepSASTFindingToSemgrepDeploymentRelProperties = (
        SemgrepSASTFindingToSemgrepDeploymentRelProperties()
    )


@dataclass(frozen=True)
class SemgrepSASTFindingToGithubRepoRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:SemgrepSASTFinding)-[:FOUND_IN]->(:GitHubRepository)
class SemgrepSASTFindingToGithubRepoRel(CartographyRelSchema):
    """Links a SAST finding to the GitHub repository containing the affected code."""

    target_node_label: str = "GitHubRepository"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("repositoryUrl")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "FOUND_IN"
    properties: SemgrepSASTFindingToGithubRepoRelProperties = (
        SemgrepSASTFindingToGithubRepoRelProperties()
    )


@dataclass(frozen=True)
class SemgrepSASTFindingToGitLabProjectRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:SemgrepSASTFinding)-[:FOUND_IN]->(:GitLabProject)
class SemgrepSASTFindingToGitLabProjectRel(CartographyRelSchema):
    """Links a SAST finding to the GitLab project containing the affected code."""

    target_node_label: str = "GitLabProject"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"web_url": PropertyRef("repositoryUrl")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "FOUND_IN"
    properties: SemgrepSASTFindingToGitLabProjectRelProperties = (
        SemgrepSASTFindingToGitLabProjectRelProperties()
    )


@dataclass(frozen=True)
class SemgrepSASTFindingToAssistantRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:SemgrepSASTFinding)-[:HAS_ASSISTANT]->(:SemgrepFindingAssistant)
class SemgrepSASTFindingToAssistantRel(CartographyRelSchema):
    """Links a cloud SAST finding to its Semgrep Assistant analysis."""

    target_node_label: str = "SemgrepFindingAssistant"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("assistantId")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "HAS_ASSISTANT"
    properties: SemgrepSASTFindingToAssistantRelProperties = (
        SemgrepSASTFindingToAssistantRelProperties()
    )


@dataclass(frozen=True)
class SemgrepSASTFindingSchema(CartographyNodeSchema):
    """A code-level security issue reported by Semgrep Cloud or Semgrep OSS."""

    label: str = "SemgrepSASTFinding"
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(["SecurityIssue"])
    properties: SemgrepSASTFindingNodeProperties = SemgrepSASTFindingNodeProperties()
    sub_resource_relationship: SemgrepSASTFindingToSemgrepDeploymentRel = (
        SemgrepSASTFindingToSemgrepDeploymentRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            SemgrepSASTFindingToGithubRepoRel(),
            SemgrepSASTFindingToGitLabProjectRel(),
            SemgrepSASTFindingToAssistantRel(),
        ],
    )

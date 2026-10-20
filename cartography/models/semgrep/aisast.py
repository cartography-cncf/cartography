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
class SemgrepAISASTFindingNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "id",
        description="Unique finding identifier from Semgrep Cloud.",
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    rule_id: PropertyRef = PropertyRef(
        "ruleId",
        extra_index=True,
        description="Name of the AI-powered detection rule that triggered the finding.",
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
    ai_impact: PropertyRef = PropertyRef(
        "aiImpact",
        description="AI-generated description of the potential impact if the vulnerability is exploited.",
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
    subcategories: PropertyRef = PropertyRef(
        "subcategories",
        description="Subcategories associated with the rule.",
    )
    vulnerability_classes: PropertyRef = PropertyRef(
        "vulnerabilityClasses",
        description="Vulnerability classes associated with the rule.",
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
        description="URL of the affected line of code.",
    )
    match_based_id: PropertyRef = PropertyRef(
        "matchBasedId",
        description="Identifier derived from the finding's file path, rule, and pattern, stable across scans.",
    )
    state: PropertyRef = PropertyRef(
        "state",
        description="Current finding state as detected by scans (`unresolved`, `fixed`, or `muted`).",
    )
    fix_status: PropertyRef = PropertyRef(
        "fixStatus",
        description="Finding status combining scan state and triage (for example `open`, `fixed`, `ignored`).",
    )
    triage_status: PropertyRef = PropertyRef(
        "triageStatus",
        description="Finding triage state (for example `untriaged`, `ignored`, `reopened`).",
    )
    triage_reason: PropertyRef = PropertyRef(
        "triageReason",
        description="Reason provided when the finding was triaged.",
    )
    triaged_at: PropertyRef = PropertyRef(
        "triagedAt",
        description="UTC date and time when the finding was triaged.",
    )
    opened_at: PropertyRef = PropertyRef(
        "openedAt",
        description="UTC date and time when the finding was opened.",
    )
    relevant_since: PropertyRef = PropertyRef(
        "relevantSince",
        description="UTC date and time when Semgrep first detected the finding, or detected it again after reintroduction.",
    )


@dataclass(frozen=True)
class SemgrepAISASTFindingToSemgrepDeploymentRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:SemgrepAISASTFinding)<-[:RESOURCE]-(:SemgrepDeployment)
class SemgrepAISASTFindingToSemgrepDeploymentRel(CartographyRelSchema):
    """Connects a Semgrep deployment to one of its AI SAST findings."""

    target_node_label: str = "SemgrepDeployment"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("DEPLOYMENT_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: SemgrepAISASTFindingToSemgrepDeploymentRelProperties = (
        SemgrepAISASTFindingToSemgrepDeploymentRelProperties()
    )


@dataclass(frozen=True)
class SemgrepAISASTFindingToGithubRepoRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:SemgrepAISASTFinding)-[:FOUND_IN]->(:GitHubRepository)
class SemgrepAISASTFindingToGithubRepoRel(CartographyRelSchema):
    """Links an AI SAST finding to the GitHub repository containing the affected code."""

    target_node_label: str = "GitHubRepository"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("repositoryUrl")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "FOUND_IN"
    properties: SemgrepAISASTFindingToGithubRepoRelProperties = (
        SemgrepAISASTFindingToGithubRepoRelProperties()
    )


@dataclass(frozen=True)
class SemgrepAISASTFindingToGitLabProjectRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:SemgrepAISASTFinding)-[:FOUND_IN]->(:GitLabProject)
class SemgrepAISASTFindingToGitLabProjectRel(CartographyRelSchema):
    """Links an AI SAST finding to the GitLab project containing the affected code."""

    target_node_label: str = "GitLabProject"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"web_url": PropertyRef("repositoryUrl")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "FOUND_IN"
    properties: SemgrepAISASTFindingToGitLabProjectRelProperties = (
        SemgrepAISASTFindingToGitLabProjectRelProperties()
    )


@dataclass(frozen=True)
class SemgrepAISASTFindingToAssistantRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:SemgrepAISASTFinding)-[:HAS_ASSISTANT]->(:SemgrepFindingAssistant)
class SemgrepAISASTFindingToAssistantRel(CartographyRelSchema):
    """Links an AI SAST finding to its Semgrep Assistant analysis."""

    target_node_label: str = "SemgrepFindingAssistant"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("assistantId")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "HAS_ASSISTANT"
    properties: SemgrepAISASTFindingToAssistantRelProperties = (
        SemgrepAISASTFindingToAssistantRelProperties()
    )


@dataclass(frozen=True)
class SemgrepAISASTFindingSchema(CartographyNodeSchema):
    """A code-level security issue detected by Semgrep's AI-powered detection (`ai_sast`)."""

    label: str = "SemgrepAISASTFinding"
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels([SECURITY_ISSUE])
    properties: SemgrepAISASTFindingNodeProperties = (
        SemgrepAISASTFindingNodeProperties()
    )
    sub_resource_relationship: SemgrepAISASTFindingToSemgrepDeploymentRel = (
        SemgrepAISASTFindingToSemgrepDeploymentRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            SemgrepAISASTFindingToGithubRepoRel(),
            SemgrepAISASTFindingToGitLabProjectRel(),
            SemgrepAISASTFindingToAssistantRel(),
        ],
    )

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
class OSSSemgrepSASTFindingNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "id",
        description="Unique finding identifier from Semgrep Cloud or synthesized for an OSS finding.",
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    rule_id: PropertyRef = PropertyRef(
        "check_id",
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

    description: PropertyRef = PropertyRef(
        "extra.message",
        description="Description of the vulnerability from the rule message.",
    )
    severity: PropertyRef = PropertyRef(
        "extra.severity",
        description="Severity assigned to the finding.",
    )
    confidence: PropertyRef = PropertyRef(
        "extra.metadata.confidence",
        description="Confidence assigned to the finding.",
    )
    file_path: PropertyRef = PropertyRef(
        "path",
        extra_index=True,
        description="Path of the file where the finding was discovered.",
    )
    start_line: PropertyRef = PropertyRef(
        "start.line",
        description="Line where the finding starts.",
    )
    start_col: PropertyRef = PropertyRef(
        "start.col",
        description="Column where the finding starts.",
    )
    end_line: PropertyRef = PropertyRef(
        "end.line",
        description="Line where the finding ends.",
    )
    end_col: PropertyRef = PropertyRef(
        "end.col",
        description="Column where the finding ends.",
    )
    cwe_names: PropertyRef = PropertyRef(
        "extra.metadata.cwe",
        description="CWE identifiers associated with the rule.",
    )
    owasp_names: PropertyRef = PropertyRef(
        "extra.metadata.owasp",
        description="OWASP category names associated with the rule.",
    )
    categories: PropertyRef = PropertyRef(
        "categories",
        description="Categories associated with the finding.",
    )
    title: PropertyRef = PropertyRef(
        "check_id",
        description="Short title for the finding.",
    )


@dataclass(frozen=True)
class OSSSemgrepSASTFindingToSemgrepDeploymentRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:SemgrepSASTFinding)<-[:RESOURCE]-(:SemgrepDeployment)
class OSSSemgrepSASTFindingToSemgrepDeploymentRel(CartographyRelSchema):
    """Connects a Semgrep deployment to one of its SAST findings."""

    target_node_label: str = "SemgrepDeployment"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("DEPLOYMENT_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: OSSSemgrepSASTFindingToSemgrepDeploymentRelProperties = (
        OSSSemgrepSASTFindingToSemgrepDeploymentRelProperties()
    )


@dataclass(frozen=True)
class OSSSemgrepSASTFindingToGithubRepoRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:SemgrepSASTFinding)-[:FOUND_IN]->(:GitHubRepository)
class OSSSemgrepSASTFindingToGithubRepoRel(CartographyRelSchema):
    """Links a SAST finding to the GitHub repository containing the affected code."""

    target_node_label: str = "GitHubRepository"
    # GitHubRepository.id stores the repository URL, so repositoryUrl is the join key.
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("repositoryUrl")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "FOUND_IN"
    properties: OSSSemgrepSASTFindingToGithubRepoRelProperties = (
        OSSSemgrepSASTFindingToGithubRepoRelProperties()
    )


@dataclass(frozen=True)
class OSSSemgrepSASTFindingToGitLabProjectRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:SemgrepSASTFinding)-[:FOUND_IN]->(:GitLabProject)
class OSSSemgrepSASTFindingToGitLabProjectRel(CartographyRelSchema):
    """Links a SAST finding to the GitLab project containing the affected code."""

    target_node_label: str = "GitLabProject"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"web_url": PropertyRef("repositoryUrl")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "FOUND_IN"
    properties: OSSSemgrepSASTFindingToGitLabProjectRelProperties = (
        OSSSemgrepSASTFindingToGitLabProjectRelProperties()
    )


@dataclass(frozen=True)
class OSSSemgrepSASTFindingSchema(CartographyNodeSchema):
    """A code-level security issue reported by Semgrep Cloud or Semgrep OSS."""

    label: str = "SemgrepSASTFinding"
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(["SecurityIssue"])
    properties: OSSSemgrepSASTFindingNodeProperties = (
        OSSSemgrepSASTFindingNodeProperties()
    )
    sub_resource_relationship: OSSSemgrepSASTFindingToSemgrepDeploymentRel = (
        OSSSemgrepSASTFindingToSemgrepDeploymentRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            OSSSemgrepSASTFindingToGithubRepoRel(),
            OSSSemgrepSASTFindingToGitLabProjectRel(),
        ],
    )

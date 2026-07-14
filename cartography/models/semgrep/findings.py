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
class SemgrepSCAFindingNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "id",
        description="Unique identifier for the finding from the Semgrep API.",
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
    summary: PropertyRef = PropertyRef(
        "title",
        extra_index=True,
        description="Short title summarizing the finding.",
    )
    description: PropertyRef = PropertyRef(
        "description",
        description="Description of the dependency vulnerability.",
    )
    package_manager: PropertyRef = PropertyRef(
        "ecosystem",
        description="Package ecosystem of the affected dependency.",
    )
    severity: PropertyRef = PropertyRef(
        "severity",
        description="Severity assigned by Semgrep.",
    )
    cve_id: PropertyRef = PropertyRef(
        "cveId",
        extra_index=True,
        description="CVE identifier associated with the vulnerability.",
    )
    reachability_check: PropertyRef = PropertyRef(
        "reachability",
        description="Semgrep's determination of whether reachability was confirmed.",
    )
    reachability_condition: PropertyRef = PropertyRef(
        "reachableIf",
        description="Condition under which the vulnerable code is reachable.",
    )
    reachability: PropertyRef = PropertyRef(
        "exposureType",
        description="Whether the vulnerable dependency is reachable.",
    )
    transitivity: PropertyRef = PropertyRef(
        "transitivity",
        description="Whether the affected dependency is direct or transitive.",
    )
    dependency: PropertyRef = PropertyRef(
        "matchedDependency",
        description="Affected dependency name and version.",
    )
    dependency_fix: PropertyRef = PropertyRef(
        "closestSafeDependency",
        description="Closest dependency version that fixes the vulnerability.",
    )
    ref_urls: PropertyRef = PropertyRef(
        "ref_urls",
        description="Reference URLs associated with the finding.",
    )
    dependency_file: PropertyRef = PropertyRef(
        "dependencyFileLocation_path",
        extra_index=True,
        description="Path of the dependency manifest containing the vulnerable package.",
    )
    dependency_file_url: PropertyRef = PropertyRef(
        "dependencyFileLocation_url",
        extra_index=True,
        description="URL of the dependency manifest containing the vulnerable package.",
    )
    scan_time: PropertyRef = PropertyRef(
        "openedAt",
        description="UTC date and time when the finding was discovered.",
    )
    fix_status: PropertyRef = PropertyRef(
        "fixStatus",
        description="Fix status based on finding triage.",
    )
    triage_status: PropertyRef = PropertyRef(
        "triageStatus",
        description="Current triage status of the finding.",
    )
    confidence: PropertyRef = PropertyRef(
        "confidence",
        description="Confidence assigned by Semgrep.",
    )


@dataclass(frozen=True)
class SemgrepSCAFindingToSemgrepDeploymentRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:SemgrepSCAFinding)<-[:RESOURCE]-(:SemgrepDeployment)
class SemgrepSCAFindingToSemgrepDeploymentRel(CartographyRelSchema):
    """Connects a Semgrep deployment to one of its SCA findings."""

    target_node_label: str = "SemgrepDeployment"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("DEPLOYMENT_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: SemgrepSCAFindingToSemgrepDeploymentRelProperties = (
        SemgrepSCAFindingToSemgrepDeploymentRelProperties()
    )


@dataclass(frozen=True)
class SemgrepSCAFindingToGithubRepoRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:SemgrepSCAFinding)-[:FOUND_IN]->(:GitHubRepository)
class SemgrepSCAFindingToGithubRepoRel(CartographyRelSchema):
    """Links an SCA finding to the GitHub repository containing the dependency."""

    target_node_label: str = "GitHubRepository"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("repositoryUrl")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "FOUND_IN"
    properties: SemgrepSCAFindingToGithubRepoRelProperties = (
        SemgrepSCAFindingToGithubRepoRelProperties()
    )


@dataclass(frozen=True)
class SemgrepSCAFindingToGitLabProjectRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:SemgrepSCAFinding)-[:FOUND_IN]->(:GitLabProject)
class SemgrepSCAFindingToGitLabProjectRel(CartographyRelSchema):
    """Links an SCA finding to the GitLab project containing the dependency."""

    target_node_label: str = "GitLabProject"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"web_url": PropertyRef("repositoryUrl")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "FOUND_IN"
    properties: SemgrepSCAFindingToGitLabProjectRelProperties = (
        SemgrepSCAFindingToGitLabProjectRelProperties()
    )


@dataclass(frozen=True)
class SemgrepSCAFindngToDependencyRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:SemgrepSCAFinding)-[:AFFECTS]->(:Dependency)
class SemgrepSCAFindingToDependencyRel(CartographyRelSchema):
    """Links an SCA finding to the affected dependency observation."""

    target_node_label: str = "Dependency"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("matchedDependency")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "AFFECTS"
    properties: SemgrepSCAFindngToDependencyRelProperties = (
        SemgrepSCAFindngToDependencyRelProperties()
    )


@dataclass(frozen=True)
class SemgrepSCAFindingToCVERelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:SemgrepSCAFinding)<-[:LINKED_TO]-(:CVE)
class SemgrepSCAFindingToCVERel(CartographyRelSchema):
    """Links a CVE to the Semgrep SCA finding that identified it."""

    target_node_label: str = "CVE"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("cveId")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "LINKED_TO"
    properties: SemgrepSCAFindingToCVERelProperties = (
        SemgrepSCAFindingToCVERelProperties()
    )


@dataclass(frozen=True)
class SemgrepSCAFindingToAssistantRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:SemgrepSCAFinding)-[:HAS_ASSISTANT]->(:SemgrepFindingAssistant)
class SemgrepSCAFindingToAssistantRel(CartographyRelSchema):
    """Links an SCA finding to its Semgrep Assistant analysis."""

    target_node_label: str = "SemgrepFindingAssistant"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("assistantId")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "HAS_ASSISTANT"
    properties: SemgrepSCAFindingToAssistantRelProperties = (
        SemgrepSCAFindingToAssistantRelProperties()
    )


@dataclass(frozen=True)
class SemgrepSCAFindingSchema(CartographyNodeSchema):
    """A dependency vulnerability discovered by Semgrep Supply Chain."""

    label: str = "SemgrepSCAFinding"
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(["SecurityIssue"])
    properties: SemgrepSCAFindingNodeProperties = SemgrepSCAFindingNodeProperties()
    sub_resource_relationship: SemgrepSCAFindingToSemgrepDeploymentRel = (
        SemgrepSCAFindingToSemgrepDeploymentRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            SemgrepSCAFindingToGithubRepoRel(),
            SemgrepSCAFindingToGitLabProjectRel(),
            SemgrepSCAFindingToDependencyRel(),
            SemgrepSCAFindingToCVERel(),
            SemgrepSCAFindingToAssistantRel(),
        ],
    )

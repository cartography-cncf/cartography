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
from cartography.models.ontology.labels import CVE
from cartography.models.ontology.labels import SECURITY_ISSUE


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
        description=(
            "Severity assigned by Semgrep. The finding's `SemgrepSCAVulnerability` "
            "carries the same value."
        ),
    )
    cve_id: PropertyRef = PropertyRef(
        "cveId",
        extra_index=True,
        description="CVE identifier associated with the vulnerability.",
    )
    # DEPRECATED: ghsa_id moved to SemgrepSCAVulnerability; the copy on the finding
    # will be removed in v1.0.0.
    ghsa_id: PropertyRef = PropertyRef(
        "ghsaId",
        extra_index=True,
        description=(
            "Deprecated: read `ghsa_id` on the finding's `SemgrepSCAVulnerability`. "
            "GHSA advisory identifier when the finding is not CVE-backed."
        ),
    )
    has_cve: PropertyRef = PropertyRef(
        "has_cve",
        description=(
            "`true` when `cve_id` holds a CVE identifier. An advisory-only finding "
            "(`false`) is labeled `:SecurityIssue`."
        ),
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
    # DEPRECATED: ref_urls moved to SemgrepSCAVulnerability; the copy on the finding
    # will be removed in v1.0.0.
    ref_urls: PropertyRef = PropertyRef(
        "ref_urls",
        description=(
            "Deprecated: read `ref_urls` on the finding's `SemgrepSCAVulnerability`. "
            "Reference URLs associated with the finding."
        ),
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
class SemgrepSCAFindingToVulnerabilityRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:SemgrepSCAFinding)-[:HAS_VULNERABILITY]->(:SemgrepSCAVulnerability)
class SemgrepSCAFindingToVulnerabilityRel(CartographyRelSchema):
    """Links an SCA finding to the vulnerability it reports."""

    target_node_label: str = "SemgrepSCAVulnerability"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("vulnerabilityId")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "HAS_VULNERABILITY"
    properties: SemgrepSCAFindingToVulnerabilityRelProperties = (
        SemgrepSCAFindingToVulnerabilityRelProperties()
    )


@dataclass(frozen=True)
class SemgrepSCAFindingToCVERelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


# DEPRECATED: findings reach their CVE through HAS_VULNERABILITY; LINKED_TO will be
# removed in v1.0.0.
@dataclass(frozen=True)
# (:SemgrepSCAFinding)<-[:LINKED_TO]-(:CVE)
class SemgrepSCAFindingToCVERel(CartographyRelSchema):
    """Deprecated: links any `:CVE` node whose `id` is the finding's `cve_id` to the finding. Follow `HAS_VULNERABILITY` to the finding's `SemgrepSCAVulnerability` instead."""

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
    """A dependency vulnerability that Semgrep Supply Chain found in one repository.

    Advisory-only findings, whose identifier is not a CVE, are labeled `:SecurityIssue`. A CVE-backed finding is not itself labeled [`CVE`](#ontology-cve): the `SemgrepSCAVulnerability` it links to through `HAS_VULNERABILITY` carries that label, so each CVE is one node per deployment.
    """

    label: str = "SemgrepSCAFinding"
    # The :CVE label lives on SemgrepSCAVulnerability, one node per advisory.
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(
        [SECURITY_ISSUE.when(has_cve="false")],
    )
    properties: SemgrepSCAFindingNodeProperties = SemgrepSCAFindingNodeProperties()
    sub_resource_relationship: SemgrepSCAFindingToSemgrepDeploymentRel = (
        SemgrepSCAFindingToSemgrepDeploymentRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            SemgrepSCAFindingToGithubRepoRel(),
            SemgrepSCAFindingToGitLabProjectRel(),
            SemgrepSCAFindingToDependencyRel(),
            SemgrepSCAFindingToVulnerabilityRel(),
            SemgrepSCAFindingToCVERel(),
            SemgrepSCAFindingToAssistantRel(),
        ],
    )


@dataclass(frozen=True)
class SemgrepSCAVulnerabilityNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "id",
        description=(
            "`SEMGREP|<deployment id>|<advisory identifier>`, such as "
            "`SEMGREP|123456|CVE-2022-31129`. Each deployment has its own node per "
            "advisory, so cleanup of one deployment never deletes another's. The "
            "prefix keeps the node apart from other sources' `:CVE` nodes, which use "
            "the bare CVE identifier as their `id`."
        ),
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    cve_id: PropertyRef = PropertyRef(
        "cveId",
        extra_index=True,
        description="CVE identifier of the advisory. Unset for a GHSA advisory.",
    )
    ghsa_id: PropertyRef = PropertyRef(
        "ghsaId",
        extra_index=True,
        description="GHSA identifier of the advisory. Unset for a CVE.",
    )
    has_cve: PropertyRef = PropertyRef(
        "has_cve",
        description="`true` when the advisory is a CVE, so the node is labeled `:CVE`.",
    )
    severity: PropertyRef = PropertyRef(
        "severity",
        description="Severity that Semgrep assigns to the advisory.",
    )
    ref_urls: PropertyRef = PropertyRef(
        "ref_urls",
        description="Reference URLs for the advisory, such as its NVD or GitHub Advisory page.",
    )


@dataclass(frozen=True)
class SemgrepSCAVulnerabilityToSemgrepDeploymentRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:SemgrepSCAVulnerability)<-[:RESOURCE]-(:SemgrepDeployment)
class SemgrepSCAVulnerabilityToSemgrepDeploymentRel(CartographyRelSchema):
    """Scopes each vulnerability to the Semgrep deployment that reported it."""

    target_node_label: str = "SemgrepDeployment"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("DEPLOYMENT_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: SemgrepSCAVulnerabilityToSemgrepDeploymentRelProperties = (
        SemgrepSCAVulnerabilityToSemgrepDeploymentRelProperties()
    )


@dataclass(frozen=True)
class SemgrepSCAVulnerabilitySchema(CartographyNodeSchema):
    """An advisory, a CVE or a GHSA, that Semgrep Supply Chain reports in a deployment's SCA findings.

    Holds the advisory data that is the same for every finding of the advisory, so `CVEMetadata` enriches one node per CVE and deployment rather than every finding. Labeled [`CVE`](#ontology-cve) when the advisory is a CVE. Semgrep can report one advisory through several rules whose messages differ, so the rule message stays on each `SemgrepSCAFinding` as its `description`.
    """

    label: str = "SemgrepSCAVulnerability"
    properties: SemgrepSCAVulnerabilityNodeProperties = (
        SemgrepSCAVulnerabilityNodeProperties()
    )
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels([CVE.when(has_cve="true")])
    sub_resource_relationship: SemgrepSCAVulnerabilityToSemgrepDeploymentRel = (
        SemgrepSCAVulnerabilityToSemgrepDeploymentRel()
    )

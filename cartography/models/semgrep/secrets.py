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
class SemgrepSecretsFindingNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "id",
        description="Unique identifier for the finding from the Semgrep API.",
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    rule_hash_id: PropertyRef = PropertyRef(
        "ruleHashId",
        extra_index=True,
        description="Hash identifier of the rule that triggered the finding.",
    )
    repository_name: PropertyRef = PropertyRef(
        "repositoryName",
        extra_index=True,
        description="Repository path where the secret was discovered.",
    )
    repository_url: PropertyRef = PropertyRef(
        "repositoryUrl",
        description="Full URL of the repository where the secret was discovered.",
    )
    ref: PropertyRef = PropertyRef(
        "ref",
        description="Branch or ref where the secret was discovered.",
    )
    severity: PropertyRef = PropertyRef(
        "severity",
        extra_index=True,
        description="Severity assigned to the finding.",
    )
    confidence: PropertyRef = PropertyRef(
        "confidence",
        description="Confidence assigned to the finding.",
    )
    type: PropertyRef = PropertyRef(
        "type",
        extra_index=True,
        description="Type of secret detected.",
    )
    validation_state: PropertyRef = PropertyRef(
        "validationState",
        extra_index=True,
        description="Result of validating whether the secret is active.",
    )
    status: PropertyRef = PropertyRef(
        "status",
        extra_index=True,
        description="Current status of the finding.",
    )
    finding_path: PropertyRef = PropertyRef(
        "findingPath",
        extra_index=True,
        description="File path and line number where the secret was discovered.",
    )
    finding_path_url: PropertyRef = PropertyRef(
        "findingPathUrl",
        description="URL of the exact location where the secret was discovered.",
    )
    ref_url: PropertyRef = PropertyRef(
        "refUrl",
        description="URL of the branch or ref containing the secret.",
    )
    mode: PropertyRef = PropertyRef(
        "mode",
        description="Semgrep mode under which the secret was detected.",
    )
    created_at: PropertyRef = PropertyRef(
        "createdAt",
        description="UTC date and time when the finding was created.",
    )
    updated_at: PropertyRef = PropertyRef(
        "updatedAt",
        description="UTC date and time when the finding was last updated.",
    )
    repository_visibility: PropertyRef = PropertyRef(
        "repositoryVisibility",
        description="Visibility of the repository.",
    )
    repository_scm_type: PropertyRef = PropertyRef(
        "repositoryScmType",
        description="Source control system hosting the repository.",
    )


@dataclass(frozen=True)
class SemgrepSecretsFindingToSemgrepDeploymentRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:SemgrepSecretsFinding)<-[:RESOURCE]-(:SemgrepDeployment)
class SemgrepSecretsFindingToSemgrepDeploymentRel(CartographyRelSchema):
    """Connects a Semgrep deployment to one of its secret findings."""

    target_node_label: str = "SemgrepDeployment"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("DEPLOYMENT_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: SemgrepSecretsFindingToSemgrepDeploymentRelProperties = (
        SemgrepSecretsFindingToSemgrepDeploymentRelProperties()
    )


@dataclass(frozen=True)
class SemgrepSecretsFindingToGithubRepoRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:SemgrepSecretsFinding)-[:FOUND_IN]->(:GitHubRepository)
class SemgrepSecretsFindingToGithubRepoRel(CartographyRelSchema):
    """Links a secret finding to the GitHub repository containing the secret."""

    target_node_label: str = "GitHubRepository"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("repositoryUrl")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "FOUND_IN"
    properties: SemgrepSecretsFindingToGithubRepoRelProperties = (
        SemgrepSecretsFindingToGithubRepoRelProperties()
    )


@dataclass(frozen=True)
class SemgrepSecretsFindingToGitLabProjectRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:SemgrepSecretsFinding)-[:FOUND_IN]->(:GitLabProject)
class SemgrepSecretsFindingToGitLabProjectRel(CartographyRelSchema):
    """Links a secret finding to the GitLab project containing the secret."""

    target_node_label: str = "GitLabProject"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"web_url": PropertyRef("repositoryUrl")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "FOUND_IN"
    properties: SemgrepSecretsFindingToGitLabProjectRelProperties = (
        SemgrepSecretsFindingToGitLabProjectRelProperties()
    )


@dataclass(frozen=True)
class SemgrepSecretsFindingSchema(CartographyNodeSchema):
    """A hardcoded secret discovered by Semgrep in source code."""

    label: str = "SemgrepSecretsFinding"
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(["SecurityIssue"])
    properties: SemgrepSecretsFindingNodeProperties = (
        SemgrepSecretsFindingNodeProperties()
    )
    sub_resource_relationship: SemgrepSecretsFindingToSemgrepDeploymentRel = (
        SemgrepSecretsFindingToSemgrepDeploymentRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            SemgrepSecretsFindingToGithubRepoRel(),
            SemgrepSecretsFindingToGitLabProjectRel(),
        ],
    )

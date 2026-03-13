from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.relationships import CartographyRelProperties
from cartography.models.core.relationships import CartographyRelSchema
from cartography.models.core.relationships import LinkDirection
from cartography.models.core.relationships import make_target_node_matcher
from cartography.models.core.relationships import OtherRelationships
from cartography.models.core.relationships import TargetNodeMatcher


@dataclass(frozen=True)
class SemgrepSecretsFindingNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    rule_hash_id: PropertyRef = PropertyRef("ruleHashId", extra_index=True)
    repository: PropertyRef = PropertyRef("repositoryName", extra_index=True)
    branch: PropertyRef = PropertyRef("branch")
    severity: PropertyRef = PropertyRef("severity")
    confidence: PropertyRef = PropertyRef("confidence")
    secret_type: PropertyRef = PropertyRef("secretType", extra_index=True)
    validation_state: PropertyRef = PropertyRef("validationState")
    status: PropertyRef = PropertyRef("status")
    finding_path: PropertyRef = PropertyRef("findingPath", extra_index=True)
    finding_path_url: PropertyRef = PropertyRef("findingPathUrl")
    ref_url: PropertyRef = PropertyRef("refUrl")
    mode: PropertyRef = PropertyRef("mode")
    opened_at: PropertyRef = PropertyRef("openedAt")
    updated_at: PropertyRef = PropertyRef("updatedAt")
    repository_visibility: PropertyRef = PropertyRef("repositoryVisibility")
    historical_git_commit: PropertyRef = PropertyRef("historicalGitCommit")


@dataclass(frozen=True)
class SemgrepSecretsFindingToSemgrepDeploymentRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:SemgrepSecretsFinding)<-[:RESOURCE]-(:SemgrepDeployment)
class SemgrepSecretsFindingToSemgrepDeploymentRel(CartographyRelSchema):
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
    target_node_label: str = "GitHubRepository"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"fullname": PropertyRef("repositoryName")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "FOUND_IN"
    properties: SemgrepSecretsFindingToGithubRepoRelProperties = (
        SemgrepSecretsFindingToGithubRepoRelProperties()
    )


@dataclass(frozen=True)
class SemgrepSecretsFindingToAssistantRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:SemgrepSecretsFinding)-[:HAS_ASSISTANT]->(:SemgrepFindingAssistant)
class SemgrepSecretsFindingToAssistantRel(CartographyRelSchema):
    target_node_label: str = "SemgrepFindingAssistant"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("assistantId")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "HAS_ASSISTANT"
    properties: SemgrepSecretsFindingToAssistantRelProperties = (
        SemgrepSecretsFindingToAssistantRelProperties()
    )


@dataclass(frozen=True)
class SemgrepSecretsFindingSchema(CartographyNodeSchema):
    label: str = "SemgrepSecretsFinding"
    properties: SemgrepSecretsFindingNodeProperties = (
        SemgrepSecretsFindingNodeProperties()
    )
    sub_resource_relationship: SemgrepSecretsFindingToSemgrepDeploymentRel = (
        SemgrepSecretsFindingToSemgrepDeploymentRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            SemgrepSecretsFindingToGithubRepoRel(),
            SemgrepSecretsFindingToAssistantRel(),
        ],
    )

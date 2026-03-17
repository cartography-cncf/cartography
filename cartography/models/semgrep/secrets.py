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
    repository_name: PropertyRef = PropertyRef("repositoryName", extra_index=True)
    ref: PropertyRef = PropertyRef("ref")
    severity: PropertyRef = PropertyRef("severity")
    confidence: PropertyRef = PropertyRef("confidence")
    type: PropertyRef = PropertyRef("type", extra_index=True)
    validation_state: PropertyRef = PropertyRef("validationState")
    status: PropertyRef = PropertyRef("status")
    finding_path: PropertyRef = PropertyRef("findingPath", extra_index=True)
    finding_path_url: PropertyRef = PropertyRef("findingPathUrl")
    ref_url: PropertyRef = PropertyRef("refUrl")
    mode: PropertyRef = PropertyRef("mode")
    created_at: PropertyRef = PropertyRef("createdAt")
    updated_at: PropertyRef = PropertyRef("updatedAt")
    repository_visibility: PropertyRef = PropertyRef("repositoryVisibility")


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
        ],
    )

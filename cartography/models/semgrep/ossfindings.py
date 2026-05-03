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
    id: PropertyRef = PropertyRef("id")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    rule_id: PropertyRef = PropertyRef("check_id", extra_index=True)

    repository: PropertyRef = PropertyRef("repositoryName", extra_index=True)
    repository_url: PropertyRef = PropertyRef("repositoryUrl")
    branch: PropertyRef = PropertyRef("branch")

    description: PropertyRef = PropertyRef("extra.message")
    severity: PropertyRef = PropertyRef("extra.severity")
    confidence: PropertyRef = PropertyRef("extra.metadata.confidence")
    file_path: PropertyRef = PropertyRef("path", extra_index=True)
    start_line: PropertyRef = PropertyRef("start.line")
    start_col: PropertyRef = PropertyRef("start.col")
    end_line: PropertyRef = PropertyRef("end.line")
    end_col: PropertyRef = PropertyRef("end.col")
    cwe_names: PropertyRef = PropertyRef("extra.metadata.cwe")
    owasp_names: PropertyRef = PropertyRef("extra.metadata.owasp")
    categories: PropertyRef = PropertyRef("categories")
    title: PropertyRef = PropertyRef("check_id")


@dataclass(frozen=True)
class OSSSemgrepSASTFindingToSemgrepDeploymentRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:SemgrepSASTFinding)<-[:RESOURCE]-(:SemgrepDeployment)
class OSSSemgrepSASTFindingToSemgrepDeploymentRel(CartographyRelSchema):
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
    target_node_label: str = "GitHubRepository"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("repositoryUrl")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "FOUND_IN"
    properties: OSSSemgrepSASTFindingToGithubRepoRelProperties = (
        OSSSemgrepSASTFindingToGithubRepoRelProperties()
    )


@dataclass(frozen=True)
class OSSSemgrepSASTFindingSchema(CartographyNodeSchema):
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
        ],
    )

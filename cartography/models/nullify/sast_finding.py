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
class NullifySASTFindingNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    repository_id: PropertyRef = PropertyRef("repositoryId", extra_index=True)
    rule_id: PropertyRef = PropertyRef("ruleId", extra_index=True)
    title: PropertyRef = PropertyRef("title")
    category: PropertyRef = PropertyRef("category")
    message: PropertyRef = PropertyRef("message")
    severity: PropertyRef = PropertyRef("severity", extra_index=True)
    cwe: PropertyRef = PropertyRef("cwe")
    branch: PropertyRef = PropertyRef("branch")
    file_path: PropertyRef = PropertyRef("filePath")
    start_line: PropertyRef = PropertyRef("startLine")
    end_line: PropertyRef = PropertyRef("endLine")
    priority_label: PropertyRef = PropertyRef("priorityLabel")
    priority_score: PropertyRef = PropertyRef("priorityScore")
    is_resolved: PropertyRef = PropertyRef("isResolved")
    is_false_positive: PropertyRef = PropertyRef("isFalsePositive")
    is_allowlisted: PropertyRef = PropertyRef("isAllowlisted")
    created_at: PropertyRef = PropertyRef("createdAt")
    updated_at: PropertyRef = PropertyRef("updatedAt")


@dataclass(frozen=True)
class NullifySASTFindingToTenantRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:NullifyTenant)-[:RESOURCE]->(:NullifySASTFinding)
class NullifySASTFindingToTenantRel(CartographyRelSchema):
    target_node_label: str = "NullifyTenant"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("TENANT_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: NullifySASTFindingToTenantRelProperties = (
        NullifySASTFindingToTenantRelProperties()
    )


@dataclass(frozen=True)
class NullifySASTFindingToRepositoryRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:NullifySASTFinding)-[:FOUND_IN]->(:NullifyRepository)
class NullifySASTFindingToRepositoryRel(CartographyRelSchema):
    target_node_label: str = "NullifyRepository"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"repository_id": PropertyRef("repositoryId")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "FOUND_IN"
    properties: NullifySASTFindingToRepositoryRelProperties = (
        NullifySASTFindingToRepositoryRelProperties()
    )


@dataclass(frozen=True)
class NullifySASTFindingSchema(CartographyNodeSchema):
    label: str = "NullifySASTFinding"
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(["SecurityIssue"])
    properties: NullifySASTFindingNodeProperties = NullifySASTFindingNodeProperties()
    sub_resource_relationship: NullifySASTFindingToTenantRel = (
        NullifySASTFindingToTenantRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            NullifySASTFindingToRepositoryRel(),
        ],
    )

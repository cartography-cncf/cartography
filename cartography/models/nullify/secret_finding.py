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
class NullifySecretFindingNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    repository_id: PropertyRef = PropertyRef("repositoryId", extra_index=True)
    # Only the redacted value is stored; raw secrets are never ingested.
    secret_type: PropertyRef = PropertyRef("secretType", extra_index=True)
    redacted_secret: PropertyRef = PropertyRef("redactedSecret")
    rule_id: PropertyRef = PropertyRef("ruleId")
    entropy: PropertyRef = PropertyRef("entropy")
    branch: PropertyRef = PropertyRef("branch")
    file_path: PropertyRef = PropertyRef("filePath")
    start_line: PropertyRef = PropertyRef("startLine")
    end_line: PropertyRef = PropertyRef("endLine")
    author: PropertyRef = PropertyRef("author")
    commit: PropertyRef = PropertyRef("commit")
    priority_label: PropertyRef = PropertyRef("priorityLabel")
    is_false_positive: PropertyRef = PropertyRef("isFalsePositive")
    is_allowlisted: PropertyRef = PropertyRef("isAllowlisted")
    created_at: PropertyRef = PropertyRef("createdAt")
    updated_at: PropertyRef = PropertyRef("updatedAt")


@dataclass(frozen=True)
class NullifySecretFindingToTenantRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:NullifyTenant)-[:RESOURCE]->(:NullifySecretFinding)
class NullifySecretFindingToTenantRel(CartographyRelSchema):
    target_node_label: str = "NullifyTenant"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("TENANT_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: NullifySecretFindingToTenantRelProperties = (
        NullifySecretFindingToTenantRelProperties()
    )


@dataclass(frozen=True)
class NullifySecretFindingToRepositoryRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:NullifySecretFinding)-[:FOUND_IN]->(:NullifyRepository)
class NullifySecretFindingToRepositoryRel(CartographyRelSchema):
    target_node_label: str = "NullifyRepository"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"repository_id": PropertyRef("repositoryId")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "FOUND_IN"
    properties: NullifySecretFindingToRepositoryRelProperties = (
        NullifySecretFindingToRepositoryRelProperties()
    )


@dataclass(frozen=True)
class NullifySecretFindingSchema(CartographyNodeSchema):
    label: str = "NullifySecretFinding"
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(["SecurityIssue"])
    properties: NullifySecretFindingNodeProperties = (
        NullifySecretFindingNodeProperties()
    )
    sub_resource_relationship: NullifySecretFindingToTenantRel = (
        NullifySecretFindingToTenantRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            NullifySecretFindingToRepositoryRel(),
        ],
    )

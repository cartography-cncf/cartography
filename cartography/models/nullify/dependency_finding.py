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
class NullifyDependencyFindingNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    repository_id: PropertyRef = PropertyRef("repositoryId", extra_index=True)
    package: PropertyRef = PropertyRef("package", extra_index=True)
    version: PropertyRef = PropertyRef("version")
    is_direct: PropertyRef = PropertyRef("isDirect")
    suggested_version: PropertyRef = PropertyRef("suggestedVersion")
    file_path: PropertyRef = PropertyRef("packageFilePath")
    has_reachable_cves: PropertyRef = PropertyRef("hasReachableCVEs")
    max_severity: PropertyRef = PropertyRef(
        "vulnerabilitiesMaxSeverity", extra_index=True
    )
    num_critical: PropertyRef = PropertyRef("numCritical")
    num_high: PropertyRef = PropertyRef("numHigh")
    num_medium: PropertyRef = PropertyRef("numMedium")
    num_low: PropertyRef = PropertyRef("numLow")
    priority_label: PropertyRef = PropertyRef("priorityLabel")
    priority_score: PropertyRef = PropertyRef("priorityScore")
    is_resolved: PropertyRef = PropertyRef("isResolved")
    is_false_positive: PropertyRef = PropertyRef("isFalsePositive")
    is_allowlisted: PropertyRef = PropertyRef("isAllowlisted")
    created_at: PropertyRef = PropertyRef("createdAt")
    updated_at: PropertyRef = PropertyRef("updatedAt")


@dataclass(frozen=True)
class NullifyDependencyFindingToTenantRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:NullifyTenant)-[:RESOURCE]->(:NullifyDependencyFinding)
class NullifyDependencyFindingToTenantRel(CartographyRelSchema):
    target_node_label: str = "NullifyTenant"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("TENANT_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: NullifyDependencyFindingToTenantRelProperties = (
        NullifyDependencyFindingToTenantRelProperties()
    )


@dataclass(frozen=True)
class NullifyDependencyFindingToRepositoryRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:NullifyDependencyFinding)-[:FOUND_IN]->(:NullifyRepository)
class NullifyDependencyFindingToRepositoryRel(CartographyRelSchema):
    target_node_label: str = "NullifyRepository"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"repository_id": PropertyRef("repositoryId")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "FOUND_IN"
    properties: NullifyDependencyFindingToRepositoryRelProperties = (
        NullifyDependencyFindingToRepositoryRelProperties()
    )


@dataclass(frozen=True)
class NullifyDependencyFindingToCVERelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:NullifyDependencyFinding)-[:HAS_CVE]->(:CVE)
class NullifyDependencyFindingToCVERel(CartographyRelSchema):
    target_node_label: str = "CVE"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("vulnerabilitiesCVEIds", one_to_many=True)},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "HAS_CVE"
    properties: NullifyDependencyFindingToCVERelProperties = (
        NullifyDependencyFindingToCVERelProperties()
    )


@dataclass(frozen=True)
class NullifyDependencyFindingSchema(CartographyNodeSchema):
    label: str = "NullifyDependencyFinding"
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(["SecurityIssue"])
    properties: NullifyDependencyFindingNodeProperties = (
        NullifyDependencyFindingNodeProperties()
    )
    sub_resource_relationship: NullifyDependencyFindingToTenantRel = (
        NullifyDependencyFindingToTenantRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            NullifyDependencyFindingToRepositoryRel(),
            NullifyDependencyFindingToCVERel(),
        ],
    )

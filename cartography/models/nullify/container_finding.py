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
class NullifyContainerFindingNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    repository_id: PropertyRef = PropertyRef("repositoryId", extra_index=True)
    # Affected container image (flattened from imageMetadata in transform()).
    image_reference: PropertyRef = PropertyRef("_image_reference", extra_index=True)
    image_short_name: PropertyRef = PropertyRef("_image_short_name")
    image_tag: PropertyRef = PropertyRef("_image_tag")
    image_digest: PropertyRef = PropertyRef("_image_digest", extra_index=True)
    image_registry_domain: PropertyRef = PropertyRef("_image_registry_domain")
    title: PropertyRef = PropertyRef("aiTitle")
    file_path: PropertyRef = PropertyRef("filePath")
    line: PropertyRef = PropertyRef("line")
    branch: PropertyRef = PropertyRef("branch")
    commit_hash: PropertyRef = PropertyRef("commitHash")
    max_severity: PropertyRef = PropertyRef(
        "vulnerabilitiesMaxSeverity", extra_index=True
    )
    num_critical: PropertyRef = PropertyRef("numCritical")
    num_high: PropertyRef = PropertyRef("numHigh")
    num_medium: PropertyRef = PropertyRef("numMedium")
    num_low: PropertyRef = PropertyRef("numLow")
    num_unknown: PropertyRef = PropertyRef("numUnknown")
    is_auto_fixable: PropertyRef = PropertyRef("isAutoFixable")
    priority_label: PropertyRef = PropertyRef("priorityLabel")
    priority_score: PropertyRef = PropertyRef("priorityScore")
    is_resolved: PropertyRef = PropertyRef("isResolved")
    is_false_positive: PropertyRef = PropertyRef("isFalsePositive")
    is_allowlisted: PropertyRef = PropertyRef("isAllowlisted")
    created_at: PropertyRef = PropertyRef("createdAt")
    updated_at: PropertyRef = PropertyRef("updatedAt")


@dataclass(frozen=True)
class NullifyContainerFindingToTenantRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:NullifyTenant)-[:RESOURCE]->(:NullifyContainerFinding)
class NullifyContainerFindingToTenantRel(CartographyRelSchema):
    target_node_label: str = "NullifyTenant"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("TENANT_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: NullifyContainerFindingToTenantRelProperties = (
        NullifyContainerFindingToTenantRelProperties()
    )


@dataclass(frozen=True)
class NullifyContainerFindingToRepositoryRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:NullifyContainerFinding)-[:FOUND_IN]->(:NullifyRepository)
class NullifyContainerFindingToRepositoryRel(CartographyRelSchema):
    target_node_label: str = "NullifyRepository"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"repository_id": PropertyRef("repositoryId")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "FOUND_IN"
    properties: NullifyContainerFindingToRepositoryRelProperties = (
        NullifyContainerFindingToRepositoryRelProperties()
    )


@dataclass(frozen=True)
class NullifyContainerFindingToCVERelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:NullifyContainerFinding)-[:HAS_CVE]->(:CVE)
class NullifyContainerFindingToCVERel(CartographyRelSchema):
    target_node_label: str = "CVE"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("vulnerabilitiesCVEIds", one_to_many=True)},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "HAS_CVE"
    properties: NullifyContainerFindingToCVERelProperties = (
        NullifyContainerFindingToCVERelProperties()
    )


@dataclass(frozen=True)
class NullifyContainerFindingSchema(CartographyNodeSchema):
    label: str = "NullifyContainerFinding"
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(["SecurityIssue"])
    properties: NullifyContainerFindingNodeProperties = (
        NullifyContainerFindingNodeProperties()
    )
    sub_resource_relationship: NullifyContainerFindingToTenantRel = (
        NullifyContainerFindingToTenantRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            NullifyContainerFindingToRepositoryRel(),
            NullifyContainerFindingToCVERel(),
        ],
    )

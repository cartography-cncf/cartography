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
from cartography.models.sysdig.common import SysdigNodeToOntologyImageRel
from cartography.models.sysdig.common import SysdigNodeToResourceRel
from cartography.models.sysdig.common import SysdigNodeToTenantRel


@dataclass(frozen=True)
class SysdigFindingRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class SysdigFindingToPackageRel(CartographyRelSchema):
    target_node_label: str = "SysdigPackage"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"normalized_id": PropertyRef("package_normalized_id")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "AFFECTS"
    properties: SysdigFindingRelProperties = SysdigFindingRelProperties()


@dataclass(frozen=True)
class SysdigVulnerabilityFindingNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    name: PropertyRef = PropertyRef("name")
    cve_id: PropertyRef = PropertyRef("cve_id", extra_index=True)
    title: PropertyRef = PropertyRef("title")
    description: PropertyRef = PropertyRef("description")
    severity: PropertyRef = PropertyRef("severity", extra_index=True)
    status: PropertyRef = PropertyRef("status")
    fix_available: PropertyRef = PropertyRef("fix_available")
    in_use: PropertyRef = PropertyRef("in_use")
    exploit_available: PropertyRef = PropertyRef("exploit_available")
    first_seen: PropertyRef = PropertyRef("first_seen")
    last_seen: PropertyRef = PropertyRef("last_seen")
    resource_id: PropertyRef = PropertyRef("resource_id", extra_index=True)
    image_digest: PropertyRef = PropertyRef("image_digest", extra_index=True)
    package_normalized_id: PropertyRef = PropertyRef(
        "package_normalized_id", extra_index=True
    )
    package_name: PropertyRef = PropertyRef("package_name")
    package_version: PropertyRef = PropertyRef("package_version")
    package_type: PropertyRef = PropertyRef("package_type")
    url: PropertyRef = PropertyRef("url")


@dataclass(frozen=True)
class SysdigVulnerabilityFindingSchema(CartographyNodeSchema):
    label: str = "SysdigVulnerabilityFinding"
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(["Risk", "CVE"])
    properties: SysdigVulnerabilityFindingNodeProperties = (
        SysdigVulnerabilityFindingNodeProperties()
    )
    sub_resource_relationship: CartographyRelSchema = SysdigNodeToTenantRel()
    other_relationships: OtherRelationships = OtherRelationships(
        [
            SysdigNodeToResourceRel(),
            SysdigNodeToOntologyImageRel(),
            SysdigFindingToPackageRel(),
        ],
    )


@dataclass(frozen=True)
class SysdigSecurityFindingNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    title: PropertyRef = PropertyRef("title")
    severity: PropertyRef = PropertyRef("severity", extra_index=True)
    type: PropertyRef = PropertyRef("type")
    status: PropertyRef = PropertyRef("status")
    first_seen: PropertyRef = PropertyRef("first_seen")
    last_seen: PropertyRef = PropertyRef("last_seen")
    resource_id: PropertyRef = PropertyRef("resource_id", extra_index=True)
    source_entity: PropertyRef = PropertyRef("source_entity")
    url: PropertyRef = PropertyRef("url")


@dataclass(frozen=True)
class SysdigSecurityFindingSchema(CartographyNodeSchema):
    label: str = "SysdigSecurityFinding"
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(["SecurityIssue"])
    properties: SysdigSecurityFindingNodeProperties = (
        SysdigSecurityFindingNodeProperties()
    )
    sub_resource_relationship: CartographyRelSchema = SysdigNodeToTenantRel()
    other_relationships: OtherRelationships = OtherRelationships(
        [
            SysdigNodeToResourceRel(),
        ],
    )


@dataclass(frozen=True)
class SysdigRiskFindingNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    title: PropertyRef = PropertyRef("title")
    severity: PropertyRef = PropertyRef("severity", extra_index=True)
    type: PropertyRef = PropertyRef("type")
    status: PropertyRef = PropertyRef("status")
    first_seen: PropertyRef = PropertyRef("first_seen")
    last_seen: PropertyRef = PropertyRef("last_seen")
    resource_id: PropertyRef = PropertyRef("resource_id", extra_index=True)
    definition_id: PropertyRef = PropertyRef("definition_id")
    url: PropertyRef = PropertyRef("url")


@dataclass(frozen=True)
class SysdigRiskFindingSchema(CartographyNodeSchema):
    label: str = "SysdigRiskFinding"
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(["SecurityIssue"])
    properties: SysdigRiskFindingNodeProperties = SysdigRiskFindingNodeProperties()
    sub_resource_relationship: CartographyRelSchema = SysdigNodeToTenantRel()
    other_relationships: OtherRelationships = OtherRelationships(
        [
            SysdigNodeToResourceRel(),
        ],
    )


@dataclass(frozen=True)
class SysdigRuntimeEventSummaryNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    title: PropertyRef = PropertyRef("title")
    severity: PropertyRef = PropertyRef("severity", extra_index=True)
    type: PropertyRef = PropertyRef("type")
    status: PropertyRef = PropertyRef("status")
    first_seen: PropertyRef = PropertyRef("first_seen")
    last_seen: PropertyRef = PropertyRef("last_seen")
    event_count: PropertyRef = PropertyRef("event_count")
    rule_name: PropertyRef = PropertyRef("rule_name")
    rule_tags: PropertyRef = PropertyRef("rule_tags")
    policy_id: PropertyRef = PropertyRef("policy_id")
    source: PropertyRef = PropertyRef("source")
    engine: PropertyRef = PropertyRef("engine")
    resource_id: PropertyRef = PropertyRef("resource_id", extra_index=True)
    representative_event_id: PropertyRef = PropertyRef("representative_event_id")
    url: PropertyRef = PropertyRef("url")


@dataclass(frozen=True)
class SysdigRuntimeEventSummarySchema(CartographyNodeSchema):
    label: str = "SysdigRuntimeEventSummary"
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(["SecurityIssue"])
    properties: SysdigRuntimeEventSummaryNodeProperties = (
        SysdigRuntimeEventSummaryNodeProperties()
    )
    sub_resource_relationship: CartographyRelSchema = SysdigNodeToTenantRel()
    other_relationships: OtherRelationships = OtherRelationships(
        [
            SysdigNodeToResourceRel(),
        ],
    )

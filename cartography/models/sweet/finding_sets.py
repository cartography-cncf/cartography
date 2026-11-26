"""Sweet runtime vulnerability detections, stored once per distinct content.

Sweet reports one detection per workload, and workloads that run the same images
report the same findings, so storing a node per detection repeats the same data for
every workload. Here each distinct finding is a `SweetFindingContent`, each distinct
group of contents that some workload has is a `SweetFindingSet`, and each workload has
a `SweetWorkloadFindings` whose `HAS_FINDING_SET` relationship holds the IDs and times
of its own detections.
"""

from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.nodes import ExtraNodeLabels
from cartography.models.core.relationships import CartographyRelProperties
from cartography.models.core.relationships import CartographyRelSchema
from cartography.models.core.relationships import LinkDirection
from cartography.models.core.relationships import make_source_node_matcher
from cartography.models.core.relationships import make_target_node_matcher
from cartography.models.core.relationships import OtherRelationships
from cartography.models.core.relationships import SourceNodeMatcher
from cartography.models.core.relationships import TargetNodeMatcher
from cartography.models.extra_labels import RISK


@dataclass(frozen=True)
class SweetRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class SweetFindingContentNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "id",
        description="Hash of the Sweet tenant ID and the detection data that does not depend on the workload.",
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    vulnerability_id: PropertyRef = PropertyRef(
        "vulnerability_id",
        description="Identifier of the finding's vulnerability, such as a CVE or GHSA ID.",
    )
    cve_id: PropertyRef = PropertyRef(
        "cve_id",
        extra_index=True,
        description="CVE ID of the finding's vulnerability. Unset when the identifier is not a CVE.",
    )
    status: PropertyRef = PropertyRef(
        "status",
        extra_index=True,
        description="Sweet status: `open`, `in_progress`, or `ignored`.",
    )
    sweet_score: PropertyRef = PropertyRef(
        "sweet_score",
        extra_index=True,
        description="Sweet risk score from 0 to 10, which weighs runtime context.",
    )
    sweet_severity: PropertyRef = PropertyRef(
        "sweet_severity",
        extra_index=True,
        description="Sweet severity derived from the Sweet score.",
    )
    risk_indicators: PropertyRef = PropertyRef(
        "risk_indicators",
        description="Runtime risk indicators Sweet observed in the past week, such as `Loaded` or `Ingress`.",
    )
    attack_labels: PropertyRef = PropertyRef(
        "attack_labels",
        description="Attack context labels from Sweet.",
    )
    has_fix: PropertyRef = PropertyRef(
        "has_fix",
        description="Whether a fixed package version exists.",
    )
    fixed_in_versions: PropertyRef = PropertyRef(
        "fixed_in_versions",
        description="Package versions that contain the fix.",
    )
    package_name: PropertyRef = PropertyRef(
        "package_name",
        extra_index=True,
        description="Name of the vulnerable package.",
    )
    package_version: PropertyRef = PropertyRef(
        "package_version",
        description="Installed version of the vulnerable package.",
    )
    package_manager: PropertyRef = PropertyRef(
        "package_manager",
        description="Package manager or ecosystem of the vulnerable package.",
    )
    image_name: PropertyRef = PropertyRef(
        "image_name",
        description="Name of the container image that contains the package.",
    )
    image_tag: PropertyRef = PropertyRef(
        "image_tag",
        description="Tag of the container image that contains the package.",
    )
    image_digest: PropertyRef = PropertyRef(
        "image_digest",
        extra_index=True,
        description="Digest of the container image that contains the package.",
    )
    image_registry: PropertyRef = PropertyRef(
        "image_registry",
        description="Registry of the container image that contains the package.",
    )
    code_owner_name: PropertyRef = PropertyRef(
        "code_owner_name",
        description="Name of the code owner Sweet assigns to the finding.",
    )
    code_owner_email: PropertyRef = PropertyRef(
        "code_owner_email",
        description="Email of the code owner Sweet assigns to the finding.",
    )


@dataclass(frozen=True)
class SweetFindingContentToTenantRel(CartographyRelSchema):
    """Links a Sweet tenant to a finding content that it reports."""

    target_node_label: str = "SweetTenant"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("SWEET_TENANT_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: SweetRelProperties = SweetRelProperties()


@dataclass(frozen=True)
class SweetFindingContentToVulnerabilityRel(CartographyRelSchema):
    """Links a finding content to the vulnerability it reports."""

    target_node_label: str = "SweetVulnerability"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("sweet_vulnerability_id")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "HAS_VULNERABILITY"
    properties: SweetRelProperties = SweetRelProperties()


@dataclass(frozen=True)
class SweetFindingContentToImageRel(CartographyRelSchema):
    """Links a finding content to every synced copy of the container image it affects, matched on the image digest."""

    target_node_label: str = "Image"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"_ont_digest": PropertyRef("affected_image_digest")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "AFFECTS"
    properties: SweetRelProperties = SweetRelProperties()


@dataclass(frozen=True)
class SweetFindingContentSchema(CartographyNodeSchema):
    """A vulnerable package that Sweet reports on one or more running workloads.

    Holds everything in a detection that does not depend on which workload it was
    reported for. Workloads reach it through their `SweetWorkloadFindings` and
    `SweetFindingSet`.
    """

    label: str = "SweetFindingContent"
    properties: SweetFindingContentNodeProperties = SweetFindingContentNodeProperties()
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels([RISK])
    sub_resource_relationship: SweetFindingContentToTenantRel = (
        SweetFindingContentToTenantRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            SweetFindingContentToVulnerabilityRel(),
            SweetFindingContentToImageRel(),
        ],
    )


@dataclass(frozen=True)
class SweetFindingSetNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id", description="Hash of the set's `content_ids`.")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    content_ids: PropertyRef = PropertyRef(
        "content_ids",
        description=(
            "Sorted IDs of the `SweetFindingContent` nodes in the set, one entry per "
            "detection, so a content that two of a workload's detections report is "
            "listed twice. Entry k is the content of slot k."
        ),
    )


@dataclass(frozen=True)
class SweetFindingSetToTenantRel(CartographyRelSchema):
    """Links a Sweet tenant to a finding set that its workloads share."""

    target_node_label: str = "SweetTenant"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("SWEET_TENANT_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: SweetRelProperties = SweetRelProperties()


@dataclass(frozen=True)
class SweetFindingSetSchema(CartographyNodeSchema):
    """A distinct group of `SweetFindingContent` nodes that one or more workloads report.

    Workloads that run the same images usually share a set, so a new workload links to
    an existing set instead of adding a node per detection.
    """

    label: str = "SweetFindingSet"
    properties: SweetFindingSetNodeProperties = SweetFindingSetNodeProperties()
    sub_resource_relationship: SweetFindingSetToTenantRel = SweetFindingSetToTenantRel()


@dataclass(frozen=True)
class SweetFindingSetToContentRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    _sub_resource_label: PropertyRef = PropertyRef(
        "_sub_resource_label", set_in_kwargs=True
    )
    _sub_resource_id: PropertyRef = PropertyRef("_sub_resource_id", set_in_kwargs=True)
    slots: PropertyRef = PropertyRef(
        "slots",
        description=(
            "Positions of this content in the set. For a workload on the set, entry k "
            "of each list on its `HAS_FINDING_SET` relationship belongs to slot k."
        ),
    )


@dataclass(frozen=True)
class SweetFindingSetToContentMatchLink(CartographyRelSchema):
    """Links a finding set to each finding content in it, at the content's slots."""

    target_node_label: str = "SweetFindingContent"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("contentid")},
    )
    source_node_label: str = "SweetFindingSet"
    source_node_matcher: SourceNodeMatcher = make_source_node_matcher(
        {"id": PropertyRef("setid")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "CONTAINS"
    properties: SweetFindingSetToContentRelProperties = (
        SweetFindingSetToContentRelProperties()
    )


@dataclass(frozen=True)
class SweetWorkloadFindingsNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "id",
        description="Sweet tenant ID, cloud account, and workload name, joined by colons.",
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    workload: PropertyRef = PropertyRef(
        "workload",
        extra_index=True,
        description="Name of the workload, such as a host or Kubernetes workload.",
    )
    cloud_account: PropertyRef = PropertyRef(
        "cloud_account",
        description="Name of the cloud account that runs the workload. Not set when Sweet reports none.",
    )
    finding_set_id: PropertyRef = PropertyRef(
        "finding_set_id",
        description=(
            "ID of the workload's current `SweetFindingSet`. Match it on the set when "
            "reading `HAS_FINDING_SET`: until cleanup runs, a workload whose findings "
            "changed also keeps its previous set."
        ),
    )


@dataclass(frozen=True)
class SweetWorkloadFindingsToTenantRel(CartographyRelSchema):
    """Links a Sweet tenant to the findings of one of its workloads."""

    target_node_label: str = "SweetTenant"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("SWEET_TENANT_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: SweetRelProperties = SweetRelProperties()


@dataclass(frozen=True)
class SweetWorkloadFindingsToSetRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    finding_ids: PropertyRef = PropertyRef(
        "finding_ids",
        description="Sweet vulnerability IDs. Entry k is the detection in slot k of the set.",
    )
    first_detected_ms: PropertyRef = PropertyRef(
        "first_detected_ms",
        description="When Sweet first detected each finding on the workload, in epoch milliseconds.",
    )
    last_detected_ms: PropertyRef = PropertyRef(
        "last_detected_ms",
        description="When Sweet last detected each finding on the workload, in epoch milliseconds.",
    )
    last_loaded_ms: PropertyRef = PropertyRef(
        "last_loaded_ms",
        description=(
            "When Sweet last saw each vulnerable package loaded into memory on the "
            "workload, in epoch milliseconds. `0` when Sweet hasn't seen it loaded."
        ),
    )
    last_executed_ms: PropertyRef = PropertyRef(
        "last_executed_ms",
        description=(
            "When Sweet last saw each vulnerable package executed on the workload, in "
            "epoch milliseconds. `0` when Sweet hasn't seen it executed."
        ),
    )


@dataclass(frozen=True)
class SweetWorkloadFindingsToSetRel(CartographyRelSchema):
    """Links a workload's findings to the finding set they share with other workloads.

    Holds the workload's own detection IDs and times, so a previous set that cleanup
    has not removed yet still reads with the detections it had.
    """

    target_node_label: str = "SweetFindingSet"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("finding_set_id")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "HAS_FINDING_SET"
    properties: SweetWorkloadFindingsToSetRelProperties = (
        SweetWorkloadFindingsToSetRelProperties()
    )


@dataclass(frozen=True)
class SweetWorkloadFindingsSchema(CartographyNodeSchema):
    """The Sweet runtime vulnerability detections of one workload, excluding resolved vulnerabilities."""

    label: str = "SweetWorkloadFindings"
    properties: SweetWorkloadFindingsNodeProperties = (
        SweetWorkloadFindingsNodeProperties()
    )
    sub_resource_relationship: SweetWorkloadFindingsToTenantRel = (
        SweetWorkloadFindingsToTenantRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [SweetWorkloadFindingsToSetRel()],
    )

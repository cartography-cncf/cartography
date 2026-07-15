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
class SSMInstancePatchNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("Id", description="The ARN of the instance patch")
    instance_id: PropertyRef = PropertyRef(
        "_instance_id", extra_index=True, description="The managed node ID."
    )
    region: PropertyRef = PropertyRef(
        "Region", set_in_kwargs=True, description="The region of the instance patch."
    )
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last time the node was updated",
    )
    title: PropertyRef = PropertyRef(
        "Title", extra_index=True, description="The title of the patch."
    )
    kb_id: PropertyRef = PropertyRef(
        "KBId",
        extra_index=True,
        description="The operating system-specific ID of the patch.",
    )
    classification: PropertyRef = PropertyRef(
        "Classification",
        description="The classification of the patch, such as SecurityUpdates, Updates, and CriticalUpdates.",
    )
    severity: PropertyRef = PropertyRef(
        "Severity",
        description="The severity of the patch such as Critical, Important, and Moderate.",
    )
    state: PropertyRef = PropertyRef(
        "State",
        description="The state of the patch on the managed node, such as INSTALLED or FAILED.",
    )
    installed_time: PropertyRef = PropertyRef(
        "InstalledTime",
        description="The date/time the patch was installed on the managed node. Not all operating systems provide this level of information.",
    )
    cve_ids: PropertyRef = PropertyRef(
        "CVEIds",
        description="The IDs of one or more Common Vulnerabilities and Exposure (CVE) issues that are resolved by the patch.",
    )


@dataclass(frozen=True)
class SSMInstancePatchToAWSAccountRelRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class SSMInstancePatchToAWSAccountRel(CartographyRelSchema):
    "Represents a `RESOURCE` relationship from `AWSAccount` to `AWSSSMInstancePatch`."

    target_node_label: str = "AWSAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("AWS_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: SSMInstancePatchToAWSAccountRelRelProperties = (
        SSMInstancePatchToAWSAccountRelRelProperties()
    )


@dataclass(frozen=True)
class SSMInstancePatchToEC2InstanceRelRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class SSMInstancePatchToEC2InstanceRel(CartographyRelSchema):
    "Represents a `HAS_PATCH` relationship from `AWSEC2Instance` to `AWSSSMInstancePatch`."

    target_node_label: str = "AWSEC2Instance"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("_instance_id")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "HAS_PATCH"
    properties: SSMInstancePatchToEC2InstanceRelRelProperties = (
        SSMInstancePatchToEC2InstanceRelRelProperties()
    )


@dataclass(frozen=True)
class SSMInstancePatchSchema(CartographyNodeSchema):
    "Represents an `AWSSSMInstancePatch` node in the AWS graph."

    label: str = "AWSSSMInstancePatch"
    # DEPRECATED: legacy SSMInstancePatch node label will be removed in v1.0.0.
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(["SSMInstancePatch"])
    properties: SSMInstancePatchNodeProperties = SSMInstancePatchNodeProperties()
    sub_resource_relationship: SSMInstancePatchToAWSAccountRel = (
        SSMInstancePatchToAWSAccountRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            SSMInstancePatchToEC2InstanceRel(),
        ],
    )

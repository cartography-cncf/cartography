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
class CloudWatchLogGroupNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("logGroupArn")
    arn: PropertyRef = PropertyRef("logGroupArn", extra_index=True)
    creation_time: PropertyRef = PropertyRef("creationTime")
    data_protection_status: PropertyRef = PropertyRef("dataProtectionStatus")
    inherited_properties: PropertyRef = PropertyRef("inheritedProperties")
    kms_key_id: PropertyRef = PropertyRef("kmsKeyId")
    log_group_arn: PropertyRef = PropertyRef("logGroupArn")
    log_group_class: PropertyRef = PropertyRef("logGroupClass")
    log_group_name: PropertyRef = PropertyRef("logGroupName")
    metric_filter_count: PropertyRef = PropertyRef("metricFilterCount")
    retention_in_days: PropertyRef = PropertyRef("retentionInDays")
    stored_bytes: PropertyRef = PropertyRef("storedBytes")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class CloudWatchLogGroupToAwsAccountRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class CloudWatchToAWSAccountRel(CartographyRelSchema):
    target_node_label: str = "AWSAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("AWS_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: CloudWatchLogGroupToAwsAccountRelProperties = (
        CloudWatchLogGroupToAwsAccountRelProperties()
    )


@dataclass(frozen=True)
class CloudWatchLogGroupToKMSKeyRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class CloudWatchLogGroupToKMSKeyRel(CartographyRelSchema):
    target_node_label: str = "KMSKey"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {
            "id": PropertyRef("kmsKeyId"),
        }
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "ENCRYPTED_BY"
    properties: CloudWatchLogGroupToKMSKeyRelProperties = (
        CloudWatchLogGroupToKMSKeyRelProperties()
    )


@dataclass(frozen=True)
class CloudWatchLogGroupSchema(CartographyNodeSchema):
    label: str = "CloudWatchLogGroup"
    properties: CloudWatchLogGroupNodeProperties = CloudWatchLogGroupNodeProperties()
    sub_resource_relationship: CloudWatchToAWSAccountRel = CloudWatchToAWSAccountRel()
    other_relationships: OtherRelationships = OtherRelationships(
        [
            CloudWatchLogGroupToKMSKeyRel(),
        ],
    )

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
class S3PolicyStatementNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "statement_id",
        description="The unique identifier for a bucket policy statement. <br>If the statement has an Sid the id will be calculated as _S3Bucket.id_/policy_statement/_index of statement in statement_/_Sid_. <br>If the statement has no Sid the id will be calculated as  _S3Bucket.id_/policy_statement/_index of statement in statement_/",
    )
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last time the node was updated",
    )
    policy_id: PropertyRef = PropertyRef(
        "policy_id", description='Optional string "Id" for the bucket\'s policy'
    )
    policy_version: PropertyRef = PropertyRef(
        "policy_version", description="Version of the bucket's policy"
    )
    bucket: PropertyRef = PropertyRef(
        "bucket", description="Name of the S3 bucket governed by the policy statement."
    )
    sid: PropertyRef = PropertyRef(
        "Sid",
        description="Optional string to label the specific bucket policy statement",
    )
    effect: PropertyRef = PropertyRef(
        "Effect", description='Specifies "Deny" or "Allow" for the policy statement'
    )
    action: PropertyRef = PropertyRef(
        "Action",
        description="Specifies permissions that policy statement applies to, as defined [here](https://docs.aws.amazon.com/AmazonS3/latest/userguide/using-with-s3-actions.html)",
    )
    resource: PropertyRef = PropertyRef(
        "Resource",
        description="Specifies the resource the bucket policy statement is based on",
    )
    principal: PropertyRef = PropertyRef(
        "Principal",
        description="Principal expression granted or denied access by the policy statement.",
    )
    condition: PropertyRef = PropertyRef(
        "Condition",
        description="Specifies conditions where permissions are granted: [examples](https://docs.aws.amazon.com/AmazonS3/latest/userguide/amazon-s3-policy-keys.html)",
    )


@dataclass(frozen=True)
class S3PolicyStatementToAWSAccountRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class S3PolicyStatementToAWSAccountRel(CartographyRelSchema):
    "Represents a `RESOURCE` relationship from `AWSAccount` to `AWSS3PolicyStatement`."

    target_node_label: str = "AWSAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("AWS_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: S3PolicyStatementToAWSAccountRelProperties = (
        S3PolicyStatementToAWSAccountRelProperties()
    )


@dataclass(frozen=True)
class S3PolicyStatementToS3BucketRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class S3PolicyStatementToS3BucketRel(CartographyRelSchema):
    "Represents a `POLICY_STATEMENT` relationship from `AWSS3Bucket` to `AWSS3PolicyStatement`."

    target_node_label: str = "AWSS3Bucket"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("bucket")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "POLICY_STATEMENT"
    properties: S3PolicyStatementToS3BucketRelProperties = (
        S3PolicyStatementToS3BucketRelProperties()
    )


@dataclass(frozen=True)
class S3PolicyStatementSchema(CartographyNodeSchema):
    "Represents an `AWSS3PolicyStatement` node in the AWS graph."

    label: str = "AWSS3PolicyStatement"
    # DEPRECATED: legacy S3PolicyStatement node label will be removed in v1.0.0.
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(["S3PolicyStatement"])
    properties: S3PolicyStatementNodeProperties = S3PolicyStatementNodeProperties()
    sub_resource_relationship: S3PolicyStatementToAWSAccountRel = (
        S3PolicyStatementToAWSAccountRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [S3PolicyStatementToS3BucketRel()],
    )

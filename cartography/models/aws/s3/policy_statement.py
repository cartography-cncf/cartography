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
class S3PolicyStatementNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("statement_id")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    policy_id: PropertyRef = PropertyRef("policy_id")
    policy_version: PropertyRef = PropertyRef("policy_version")
    bucket: PropertyRef = PropertyRef("bucket")
    sid: PropertyRef = PropertyRef("Sid")
    effect: PropertyRef = PropertyRef("Effect")
    action: PropertyRef = PropertyRef("Action")
    resource: PropertyRef = PropertyRef("Resource")
    principal: PropertyRef = PropertyRef("Principal")
    condition: PropertyRef = PropertyRef("Condition")


@dataclass(frozen=True)
class S3PolicyStatementToAWSAccountRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class S3PolicyStatementToAWSAccountRel(CartographyRelSchema):
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
    target_node_label: str = "S3Bucket"
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
    label: str = "S3PolicyStatement"
    properties: S3PolicyStatementNodeProperties = S3PolicyStatementNodeProperties()
    sub_resource_relationship: S3PolicyStatementToAWSAccountRel = (
        S3PolicyStatementToAWSAccountRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [S3PolicyStatementToS3BucketRel()],
    )

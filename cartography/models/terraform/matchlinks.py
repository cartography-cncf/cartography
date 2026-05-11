from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.relationships import CartographyRelProperties
from cartography.models.core.relationships import CartographyRelSchema
from cartography.models.core.relationships import LinkDirection
from cartography.models.core.relationships import make_source_node_matcher
from cartography.models.core.relationships import make_target_node_matcher
from cartography.models.core.relationships import SourceNodeMatcher
from cartography.models.core.relationships import TargetNodeMatcher


@dataclass(frozen=True)
class TerraformManagesRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    _sub_resource_label: PropertyRef = PropertyRef(
        "_sub_resource_label", set_in_kwargs=True
    )
    _sub_resource_id: PropertyRef = PropertyRef("_sub_resource_id", set_in_kwargs=True)
    resource_type: PropertyRef = PropertyRef("resource_type")


def _make_manages_matchlink(target_label: str) -> type:
    @dataclass(frozen=True)
    class _MatchLink(CartographyRelSchema):
        source_node_label: str = "TerraformResourceInstance"
        source_node_matcher: SourceNodeMatcher = make_source_node_matcher(
            {"id": PropertyRef("id")},
        )
        target_node_label: str = target_label
        target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
            {"id": PropertyRef("attributes_id")},
        )
        direction: LinkDirection = LinkDirection.OUTWARD
        rel_label: str = "MANAGES"
        properties: TerraformManagesRelProperties = TerraformManagesRelProperties()

    _MatchLink.__name__ = f"TerraformInstanceTo{target_label}MatchLink"
    _MatchLink.__qualname__ = _MatchLink.__name__
    return _MatchLink


TerraformInstanceToS3BucketMatchLink = _make_manages_matchlink("S3Bucket")
TerraformInstanceToEC2InstanceMatchLink = _make_manages_matchlink("EC2Instance")
TerraformInstanceToEKSClusterMatchLink = _make_manages_matchlink("EKSCluster")
TerraformInstanceToRDSInstanceMatchLink = _make_manages_matchlink("RDSInstance")
TerraformInstanceToAWSRoleMatchLink = _make_manages_matchlink("AWSRole")
TerraformInstanceToAWSManagedPolicyMatchLink = _make_manages_matchlink(
    "AWSManagedPolicy"
)
TerraformInstanceToEC2SecurityGroupMatchLink = _make_manages_matchlink(
    "EC2SecurityGroup"
)

RESOURCE_TYPE_MATCHLINKS: dict[str, CartographyRelSchema] = {
    "aws_s3_bucket": TerraformInstanceToS3BucketMatchLink(),
    "aws_instance": TerraformInstanceToEC2InstanceMatchLink(),
    "aws_eks_cluster": TerraformInstanceToEKSClusterMatchLink(),
    "aws_db_instance": TerraformInstanceToRDSInstanceMatchLink(),
    "aws_iam_role": TerraformInstanceToAWSRoleMatchLink(),
    "aws_iam_policy": TerraformInstanceToAWSManagedPolicyMatchLink(),
    "aws_security_group": TerraformInstanceToEC2SecurityGroupMatchLink(),
}

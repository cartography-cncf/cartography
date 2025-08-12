"""
Test data for IAM permissions matchlink functionality.
"""

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
class IAMAccessRelProps(CartographyRelProperties):
    """Relationship properties for IAM access permissions."""

    lastupdated: PropertyRef = PropertyRef("UPDATE_TAG", set_in_kwargs=True)
    permission_action: PropertyRef = PropertyRef("permission_action")
    _sub_resource_label: PropertyRef = PropertyRef(
        "_sub_resource_label", set_in_kwargs=True
    )
    _sub_resource_id: PropertyRef = PropertyRef("_sub_resource_id", set_in_kwargs=True)


@dataclass(frozen=True)
class PrincipalToS3BucketPermissionRel(CartographyRelSchema):
    """Test relationship schema connecting principals to S3 buckets with permissions."""

    source_node_label: str = "AWSPrincipal"
    source_node_matcher: SourceNodeMatcher = make_source_node_matcher(
        {
            "principal_arn": PropertyRef("principal_arn"),
        }
    )
    target_node_label: str = "S3Bucket"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {
            "name": PropertyRef("BucketName"),
        }
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "CAN_ACCESS"
    properties: IAMAccessRelProps = IAMAccessRelProps()

from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.relationships import CartographyRelProperties
from cartography.models.core.relationships import CartographyRelSchema
from cartography.models.core.relationships import LinkDirection
from cartography.models.core.relationships import make_target_node_matcher
from cartography.models.core.relationships import TargetNodeMatcher


@dataclass(frozen=True)
class S3BucketToSNSTopicRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class S3BucketToSNSTopicRel(CartographyRelSchema):
    target_node_label: str = "SNSTopic"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"arn": PropertyRef("TopicArn")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "NOTIFIES"
    properties: S3BucketToSNSTopicRelProperties = S3BucketToSNSTopicRelProperties()

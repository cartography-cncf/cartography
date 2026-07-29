from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.relationships import CartographyRelProperties
from cartography.models.core.relationships import CartographyRelSchema
from cartography.models.core.relationships import LinkDirection
from cartography.models.core.relationships import make_target_node_matcher
from cartography.models.core.relationships import TargetNodeMatcher


@dataclass(frozen=True)
class AWSGroupToAWSUserRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# DEPRECATED: replaced by the canonical (:UserAccount)-[:MEMBER_OF]->(:UserGroup)
# edge (AWSGroupToAWSUserMemberOfRel). Kept for backward compatibility, will be
# removed in v1.0.0.
class AWSGroupToAWSUserRel(CartographyRelSchema):
    # AWSUser -MEMBER_AWS_GROUP-> AWSGroup
    target_node_label: str = "AWSUser"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {
            "arn": PropertyRef("user_arns", one_to_many=True),
        }
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "MEMBER_AWS_GROUP"
    properties: AWSGroupToAWSUserRelProperties = AWSGroupToAWSUserRelProperties()


@dataclass(frozen=True)
class AWSGroupToAWSUserMemberOfRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# Canonical ontology edge: (:UserAccount)-[:MEMBER_OF]->(:UserGroup)
class AWSGroupToAWSUserMemberOfRel(CartographyRelSchema):
    target_node_label: str = "AWSUser"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {
            "arn": PropertyRef("user_arns", one_to_many=True),
        }
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "MEMBER_OF"
    properties: AWSGroupToAWSUserMemberOfRelProperties = (
        AWSGroupToAWSUserMemberOfRelProperties()
    )

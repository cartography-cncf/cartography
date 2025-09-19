from dataclasses import dataclass

from cartography.models.aws.iam.group_membership import AWSGroupToAWSUserRel
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
class AWSGroupNodeProperties(CartographyNodeProperties):
    # Required unique identifier
    id: PropertyRef = PropertyRef("arn")
    arn: PropertyRef = PropertyRef("arn", extra_index=True)

    # Automatic fields (set by cartography)
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)

    # Business fields from AWS IAM groups
    groupid: PropertyRef = PropertyRef("groupid")
    name: PropertyRef = PropertyRef("name")
    path: PropertyRef = PropertyRef("path")
    createdate: PropertyRef = PropertyRef("createdate")


@dataclass(frozen=True)
class AWSGroupToAWSAccountRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AWSGroupToAWSAccountRel(CartographyRelSchema):
    target_node_label: str = "AWSAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {
            "id": PropertyRef("AWS_ID", set_in_kwargs=True),
        }
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: AWSGroupToAWSAccountRelProperties = AWSGroupToAWSAccountRelProperties()


@dataclass(frozen=True)
class AWSGroupSchema(CartographyNodeSchema):
    label: str = "AWSGroup"
    properties: AWSGroupNodeProperties = AWSGroupNodeProperties()
    sub_resource_relationship: AWSGroupToAWSAccountRel = AWSGroupToAWSAccountRel()
    other_relationships: OtherRelationships = OtherRelationships(
        [
            AWSGroupToAWSUserRel(),
        ]
    )
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(["AWSPrincipal"])

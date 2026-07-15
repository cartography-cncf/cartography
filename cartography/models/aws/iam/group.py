from dataclasses import dataclass

from cartography.models.aws.iam.group_membership import AWSGroupToAWSUserMemberOfRel
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
    id: PropertyRef = PropertyRef(
        "arn", description="Unique identifier for this `AWSGroup` node."
    )
    arn: PropertyRef = PropertyRef(
        "arn",
        extra_index=True,
        description="Amazon Resource Name (ARN) of this `AWSGroup` node.",
    )

    # Automatic fields (set by cartography)
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last sync that updated this `AWSGroup` node.",
    )

    # Business fields from AWS IAM groups
    groupid: PropertyRef = PropertyRef(
        "groupid",
        description="Identifier of the group linked to this `AWSGroup` node.",
    )
    name: PropertyRef = PropertyRef("name", description="Name of this `AWSGroup` node.")
    path: PropertyRef = PropertyRef(
        "path", description="IAM path under which the IAM group is organized."
    )
    createdate: PropertyRef = PropertyRef(
        "createdate", description="Timestamp when the IAM group was created."
    )
    createdate_dt: PropertyRef = PropertyRef(
        "createdate_dt",
        description="Creation timestamp for the IAM group normalized as a Neo4j datetime.",
    )


@dataclass(frozen=True)
class AWSGroupToAWSAccountRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AWSGroupToAWSAccountRel(CartographyRelSchema):
    "Represents a `RESOURCE` relationship from `AWSAccount` to `AWSGroup`."

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
    "Represents an `AWSGroup` node in the AWS graph."

    label: str = "AWSGroup"
    properties: AWSGroupNodeProperties = AWSGroupNodeProperties()
    sub_resource_relationship: AWSGroupToAWSAccountRel = AWSGroupToAWSAccountRel()
    other_relationships: OtherRelationships = OtherRelationships(
        [
            AWSGroupToAWSUserRel(),
            AWSGroupToAWSUserMemberOfRel(),
        ]
    )
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(["AWSPrincipal", "UserGroup"])

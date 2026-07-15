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
class DBSubnetGroupNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id", description="The ARN of the AWSDBSubnetGroup")
    name: PropertyRef = PropertyRef("name", description="The name of AWSDBSubnetGroup")
    vpc_id: PropertyRef = PropertyRef(
        "vpc_id",
        description="The ID of the VPC (Virtual Private Cloud) that this DB Subnet Group is associated with.",
    )
    description: PropertyRef = PropertyRef(
        "description", description="Description of the DB Subnet Group"
    )
    status: PropertyRef = PropertyRef("status", description="The status of the group")
    region: PropertyRef = PropertyRef(
        "Region",
        set_in_kwargs=True,
        description="The AWS region where the DB Subnet Group is located.",
    )
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last time the node was updated",
    )


@dataclass(frozen=True)
class DBSubnetGroupToAWSAccountRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class DBSubnetGroupToAWSAccountRel(CartographyRelSchema):
    "Represents a `RESOURCE` relationship from `AWSAccount` to `AWSDBSubnetGroup`."

    target_node_label: str = "AWSAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("AWS_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: DBSubnetGroupToAWSAccountRelProperties = (
        DBSubnetGroupToAWSAccountRelProperties()
    )


@dataclass(frozen=True)
class DBSubnetGroupToRDSInstanceRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class DBSubnetGroupToRDSInstanceRel(CartographyRelSchema):
    "Represents a `MEMBER_OF_DB_SUBNET_GROUP` relationship from `AWSRDSInstance` to `AWSDBSubnetGroup`."

    target_node_label: str = "AWSRDSInstance"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {
            "db_instance_identifier": PropertyRef(
                "db_instance_identifier", one_to_many=True
            ),
        }
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "MEMBER_OF_DB_SUBNET_GROUP"
    properties: DBSubnetGroupToRDSInstanceRelProperties = (
        DBSubnetGroupToRDSInstanceRelProperties()
    )


@dataclass(frozen=True)
class DBSubnetGroupToEC2SubnetRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class DBSubnetGroupToEC2SubnetRel(CartographyRelSchema):
    "Represents a `RESOURCE` relationship from `AWSDBSubnetGroup` to `AWSEC2Subnet`."

    target_node_label: str = "AWSEC2Subnet"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {
            "subnetid": PropertyRef("subnet_ids", one_to_many=True),
        }
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "RESOURCE"
    properties: DBSubnetGroupToEC2SubnetRelProperties = (
        DBSubnetGroupToEC2SubnetRelProperties()
    )


@dataclass(frozen=True)
class DBSubnetGroupSchema(CartographyNodeSchema):
    """
    DB Subnet Group schema
    """

    label: str = "AWSDBSubnetGroup"
    # DEPRECATED: legacy DBSubnetGroup node label will be removed in v1.0.0.
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(["DBSubnetGroup"])
    properties: DBSubnetGroupNodeProperties = DBSubnetGroupNodeProperties()
    sub_resource_relationship: DBSubnetGroupToAWSAccountRel = (
        DBSubnetGroupToAWSAccountRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            DBSubnetGroupToRDSInstanceRel(),
            DBSubnetGroupToEC2SubnetRel(),
        ]
    )

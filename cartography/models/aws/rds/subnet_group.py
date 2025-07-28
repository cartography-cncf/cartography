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
class DBSubnetGroupNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id")
    name: PropertyRef = PropertyRef("name")
    vpc_id: PropertyRef = PropertyRef("vpc_id")
    description: PropertyRef = PropertyRef("description")
    status: PropertyRef = PropertyRef("status")
    region: PropertyRef = PropertyRef("Region", set_in_kwargs=True)
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class DBSubnetGroupToAWSAccountRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class DBSubnetGroupToAWSAccountRel(CartographyRelSchema):
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
    target_node_label: str = "RDSInstance"
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
    target_node_label: str = "EC2Subnet"
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

    label: str = "DBSubnetGroup"
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

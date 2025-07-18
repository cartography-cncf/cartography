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
class EC2SubnetRDSNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("SubnetId")
    # TODO: remove subnetid once we have migrated to subnet_id
    subnetid: PropertyRef = PropertyRef("SubnetId", extra_index=True)
    subnet_id: PropertyRef = PropertyRef("SubnetId", extra_index=True)
    region: PropertyRef = PropertyRef("Region", set_in_kwargs=True)
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    availability_zone: PropertyRef = PropertyRef("availability_zone")


@dataclass(frozen=True)
class EC2SubnetToAWSAccountRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class EC2SubnetToAWSAccountRel(CartographyRelSchema):
    target_node_label: str = "AWSAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("AWS_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: EC2SubnetToAWSAccountRelProperties = (
        EC2SubnetToAWSAccountRelProperties()
    )


@dataclass(frozen=True)
class EC2SubnetToDBSubnetGroupRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class EC2SubnetToDBSubnetGroupRel(CartographyRelSchema):
    target_node_label: str = "DBSubnetGroup"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("db_subnet_group_arn")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: EC2SubnetToDBSubnetGroupRelProperties = (
        EC2SubnetToDBSubnetGroupRelProperties()
    )


@dataclass(frozen=True)
class EC2SubnetRDSSchema(CartographyNodeSchema):
    """
    EC2 Subnet as known by RDS instances
    """

    label: str = "EC2Subnet"
    properties: EC2SubnetRDSNodeProperties = EC2SubnetRDSNodeProperties()
    sub_resource_relationship: EC2SubnetToAWSAccountRel = EC2SubnetToAWSAccountRel()
    other_relationships: OtherRelationships = OtherRelationships(
        [
            EC2SubnetToDBSubnetGroupRel(),
        ],
    )

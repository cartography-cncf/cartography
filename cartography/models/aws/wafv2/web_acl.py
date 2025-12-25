from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.relationships import CartographyRelProperties
from cartography.models.core.relationships import CartographyRelSchema
from cartography.models.core.relationships import LinkDirection
from cartography.models.core.relationships import make_target_node_matcher
from cartography.models.core.relationships import TargetNodeMatcher


@dataclass(frozen=True)
class AWSWAFv2WebACLNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("ARN")
    name: PropertyRef = PropertyRef("Name")
    web_acl_id: PropertyRef = PropertyRef("Id")
    arn: PropertyRef = PropertyRef("ARN")
    capacity: PropertyRef = PropertyRef("Capacity")
    description: PropertyRef = PropertyRef("Description")
    lock_token: PropertyRef = PropertyRef("LockToken")
    managed_by_firewall_manager: PropertyRef = PropertyRef("ManagedByFirewallManager")
    region: PropertyRef = PropertyRef("Region", set_in_kwargs=True)
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AWSWAFv2WebACLToAWSAccountRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AWSWAFv2WebACLToAWSAccountRel(CartographyRelSchema):
    target_node_label: str = "AWSAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("AWS_ID", set_in_kwargs=True)}
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: AWSWAFv2WebACLToAWSAccountRelProperties = (
        AWSWAFv2WebACLToAWSAccountRelProperties()
    )


@dataclass(frozen=True)
class AWSWAFv2WebACLSchema(CartographyNodeSchema):
    label: str = "AWSWAFv2WebACL"
    properties: AWSWAFv2WebACLNodeProperties = AWSWAFv2WebACLNodeProperties()
    sub_resource_relationship: AWSWAFv2WebACLToAWSAccountRel = (
        AWSWAFv2WebACLToAWSAccountRel()
    )

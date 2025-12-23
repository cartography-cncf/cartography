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
class AWSWAFv2RuleGroupNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("Id")
    name: PropertyRef = PropertyRef("Name")
    arn: PropertyRef = PropertyRef("ARN")
    capacity: PropertyRef = PropertyRef("Capacity")
    description: PropertyRef = PropertyRef("Description")
    lock_token: PropertyRef = PropertyRef("LockToken")
    region: PropertyRef = PropertyRef("Region", set_in_kwargs=True)
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AWSWAFv2RuleGroupToAWSAccountRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AWSWAFv2RuleGroupToAWSAccountRel(CartographyRelSchema):
    target_node_label: str = "AWSAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("AWS_ID", set_in_kwargs=True)}
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: AWSWAFv2RuleGroupToAWSAccountRelProperties = (
        AWSWAFv2RuleGroupToAWSAccountRelProperties()
    )


@dataclass(frozen=True)
class AWSWAFv2RuleGroupSchema(CartographyNodeSchema):
    label: str = "AWSWAFv2RuleGroup"
    properties: AWSWAFv2RuleGroupNodeProperties = AWSWAFv2RuleGroupNodeProperties()
    sub_resource_relationship: AWSWAFv2RuleGroupToAWSAccountRel = (
        AWSWAFv2RuleGroupToAWSAccountRel()
    )

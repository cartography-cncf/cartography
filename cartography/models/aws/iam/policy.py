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
class AWSPolicyNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    name: PropertyRef = PropertyRef("name")
    type: PropertyRef = PropertyRef("type")
    arn: PropertyRef = PropertyRef("arn", extra_index=True)
    createdate: PropertyRef = PropertyRef("createdate")


@dataclass(frozen=True)
class AWSPolicyToAWSPrincipalRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AWSPolicyToAWSPrincipalRel(CartographyRelSchema):
    target_node_label: str = "AWSPrincipal"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {
            "arn": PropertyRef("principal_arn"),
        }
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "POLICY"
    properties: AWSPolicyToAWSPrincipalRelProperties = (
        AWSPolicyToAWSPrincipalRelProperties()
    )


@dataclass(frozen=True)
class AWSPolicySchema(CartographyNodeSchema):
    label: str = "AWSPolicy"
    properties: AWSPolicyNodeProperties = AWSPolicyNodeProperties()
    # TODO consider making this to the Account. For now we're keeping the legacy structure.
    sub_resource_relationship: AWSPolicyToAWSPrincipalRel = AWSPolicyToAWSPrincipalRel()

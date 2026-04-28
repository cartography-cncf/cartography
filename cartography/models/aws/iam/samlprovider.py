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
class AWSSAMLProviderNodeProperties(CartographyNodeProperties):
    """
    Schema describing an AWS IAM SAML Provider.
    """

    # Unique identifiers
    id: PropertyRef = PropertyRef("Arn")
    arn: PropertyRef = PropertyRef("Arn", extra_index=True)

    # Business properties
    create_date: PropertyRef = PropertyRef("CreateDate")
    valid_until: PropertyRef = PropertyRef("ValidUntil")

    # Common
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AWSSAMLProviderToAWSAccountRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AWSSAMLProviderToAWSAccountRel(CartographyRelSchema):
    target_node_label: str = "AWSAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("AWS_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: AWSSAMLProviderToAWSAccountRelProperties = (
        AWSSAMLProviderToAWSAccountRelProperties()
    )


@dataclass(frozen=True)
class AWSSAMLProviderSchema(CartographyNodeSchema):
    label: str = "AWSSAMLProvider"
    properties: AWSSAMLProviderNodeProperties = AWSSAMLProviderNodeProperties()
    sub_resource_relationship: AWSSAMLProviderToAWSAccountRel = (
        AWSSAMLProviderToAWSAccountRel()
    )

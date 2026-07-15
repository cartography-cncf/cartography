from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.nodes import ExtraNodeLabels
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
    id: PropertyRef = PropertyRef(
        "Arn", description="Unique identifier for this `AWSSAMLProvider` node."
    )
    arn: PropertyRef = PropertyRef(
        "Arn",
        extra_index=True,
        description="Amazon Resource Name (ARN) of this `AWSSAMLProvider` node.",
    )

    # Business properties
    name: PropertyRef = PropertyRef(
        "Name", extra_index=True, description="Name of this `AWSSAMLProvider` node."
    )
    create_date: PropertyRef = PropertyRef(
        "CreateDate",
        description="Timestamp when the IAM SAML provider was created.",
    )
    valid_until: PropertyRef = PropertyRef(
        "ValidUntil",
        description="Timestamp when the SAML provider metadata expires.",
    )

    # Common
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last sync that updated this `AWSSAMLProvider` node.",
    )


@dataclass(frozen=True)
class AWSSAMLProviderToAWSAccountRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AWSSAMLProviderToAWSAccountRel(CartographyRelSchema):
    "Represents a `RESOURCE` relationship from `AWSAccount` to `AWSSAMLProvider`."

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
    "Represents an `AWSSAMLProvider` node in the AWS graph."

    label: str = "AWSSAMLProvider"
    properties: AWSSAMLProviderNodeProperties = AWSSAMLProviderNodeProperties()
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(["IdentityProvider"])
    sub_resource_relationship: AWSSAMLProviderToAWSAccountRel = (
        AWSSAMLProviderToAWSAccountRel()
    )

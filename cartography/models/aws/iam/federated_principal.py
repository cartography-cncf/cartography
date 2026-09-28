from dataclasses import dataclass

from cartography.models.aws.extra_labels import AWS_PRINCIPAL
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
class AWSFederatedPrincipalNodeProperties(CartographyNodeProperties):
    # Required unique identifier
    id: PropertyRef = PropertyRef(
        "arn", description="Unique identifier for this `AWSFederatedPrincipal` node."
    )
    arn: PropertyRef = PropertyRef(
        "arn",
        extra_index=True,
        description="Amazon Resource Name (ARN) of this `AWSFederatedPrincipal` node.",
    )

    # Automatic fields (set by cartography)
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)

    # Business fields from AWS IAM federated principals
    type: PropertyRef = PropertyRef(
        "type", description="Type of this `AWSFederatedPrincipal` node."
    )


@dataclass(frozen=True)
class AWSFederatedPrincipalToAWSAccountRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AWSFederatedPrincipalToAWSAccountRel(CartographyRelSchema):
    target_node_label: str = "AWSAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {
            "id": PropertyRef("AWS_ID", set_in_kwargs=True),
        }
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: AWSFederatedPrincipalToAWSAccountRelProperties = (
        AWSFederatedPrincipalToAWSAccountRelProperties()
    )


@dataclass(frozen=True)
class AWSFederatedPrincipalSchema(CartographyNodeSchema):
    """Representation of a federated principal e.g. "arn:aws:iam::123456789012:saml-provider/my-saml-provider". Federated principals are used for authentication to AWS using SAML or OpenID Connect. Federated principals are only discoverable from AWS role trust relationships."""

    label: str = "AWSFederatedPrincipal"
    properties: AWSFederatedPrincipalNodeProperties = (
        AWSFederatedPrincipalNodeProperties()
    )
    sub_resource_relationship: AWSFederatedPrincipalToAWSAccountRel = (
        AWSFederatedPrincipalToAWSAccountRel()
    )
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels([AWS_PRINCIPAL])

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
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last sync that updated this `AWSFederatedPrincipal` node.",
    )

    # Business fields from AWS IAM federated principals
    type: PropertyRef = PropertyRef(
        "type", description="Type of this `AWSFederatedPrincipal` node."
    )


@dataclass(frozen=True)
class AWSFederatedPrincipalToAWSAccountRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AWSFederatedPrincipalToAWSAccountRel(CartographyRelSchema):
    "Represents a `RESOURCE` relationship from `AWSAccount` to `AWSFederatedPrincipal`."

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
    """
    E.g. "arn:aws:iam::123456789012:saml-provider/my-saml-provider".
    """

    label: str = "AWSFederatedPrincipal"
    properties: AWSFederatedPrincipalNodeProperties = (
        AWSFederatedPrincipalNodeProperties()
    )
    sub_resource_relationship: AWSFederatedPrincipalToAWSAccountRel = (
        AWSFederatedPrincipalToAWSAccountRel()
    )
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(["AWSPrincipal"])

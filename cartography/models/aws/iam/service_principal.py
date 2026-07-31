from dataclasses import dataclass

from cartography.models.aws.extra_labels import AWS_PRINCIPAL
from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.nodes import ExtraNodeLabels
from cartography.models.ontology.labels import SERVICE_ACCOUNT


@dataclass(frozen=True)
class AWSServicePrincipalNodeProperties(CartographyNodeProperties):
    # Required unique identifier
    id: PropertyRef = PropertyRef(
        "arn", description="Unique identifier for this `AWSServicePrincipal` node."
    )
    arn: PropertyRef = PropertyRef(
        "arn",
        extra_index=True,
        description="Amazon Resource Name (ARN) of this `AWSServicePrincipal` node.",
    )

    # Automatic fields (set by cartography)
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)

    # Business fields from AWS IAM service principals
    type: PropertyRef = PropertyRef(
        "type", description="Type of this `AWSServicePrincipal` node."
    )


@dataclass(frozen=True)
class AWSServicePrincipalSchema(CartographyNodeSchema):
    """
    Represents a global AWS service principal e.g. "ec2.amazonaws.com"
    """

    label: str = "AWSServicePrincipal"
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(
        [AWS_PRINCIPAL, SERVICE_ACCOUNT]
    )
    properties: AWSServicePrincipalNodeProperties = AWSServicePrincipalNodeProperties()

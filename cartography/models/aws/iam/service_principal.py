from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.nodes import ExtraNodeLabels


@dataclass(frozen=True)
class AWSServicePrincipalNodeProperties(CartographyNodeProperties):
    # Required unique identifier
    id: PropertyRef = PropertyRef("arn")
    arn: PropertyRef = PropertyRef("arn", extra_index=True)

    # Automatic fields (set by cartography)
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)

    # Business fields from AWS IAM service principals
    type: PropertyRef = PropertyRef("type")


@dataclass(frozen=True)
class AWSServicePrincipalSchema(CartographyNodeSchema):
    """
    Represents a global AWS service principal e.g. "ec2.amazonaws.com"
    """

    label: str = "AWSServicePrincipal"
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(["AWSPrincipal"])
    properties: AWSServicePrincipalNodeProperties = AWSServicePrincipalNodeProperties()

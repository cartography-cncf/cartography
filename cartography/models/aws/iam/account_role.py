from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema


@dataclass(frozen=True)
class AWSAccountAWSRoleNodeProperties(CartographyNodeProperties):
    # Required unique identifier
    id: PropertyRef = PropertyRef("id")

    # Automatic fields (set by cartography)
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AWSAccountAWSRoleSchema(CartographyNodeSchema):
    """
    An AWSAccount that was discovered from a trusted principal in an IAM role.
    """

    label: str = "AWSAccount"
    properties: AWSAccountAWSRoleNodeProperties = AWSAccountAWSRoleNodeProperties()

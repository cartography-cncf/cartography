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
class AWSPrincipalServiceAccessNodeProperties(CartographyNodeProperties):
    """
    Composite node schema for AWSPrincipal with service last accessed details.
    This schema adds service access properties to existing AWSPrincipal nodes.
    """

    # Required unique identifier - matches existing principals by ARN
    id: PropertyRef = PropertyRef(
        "arn", description="Unique identifier for this `AWSPrincipal` node."
    )
    arn: PropertyRef = PropertyRef(
        "arn", extra_index=True, description="AWS-unique identifier for this object"
    )

    # Automatic fields (set by cartography)
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last time the node was updated",
    )

    # Service last accessed fields
    last_accessed_service_name: PropertyRef = PropertyRef(
        "last_accessed_service_name",
        description="Display name of the AWS service most recently accessed by the principal.",
    )
    last_accessed_service_namespace: PropertyRef = PropertyRef(
        "last_accessed_service_namespace",
        description="Namespace of the AWS service most recently accessed by the principal.",
    )
    last_authenticated: PropertyRef = PropertyRef(
        "last_authenticated",
        description="Timestamp when the principal last authenticated to the service.",
    )
    last_authenticated_entity: PropertyRef = PropertyRef(
        "last_authenticated_entity",
        description="ARN of the principal entity that last authenticated to the service.",
    )
    last_authenticated_region: PropertyRef = PropertyRef(
        "last_authenticated_region",
        description="AWS Region in which the principal last authenticated to the service.",
    )


@dataclass(frozen=True)
class AWSPrincipalServiceAccessToAWSAccountRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AWSPrincipalServiceAccessToAWSAccountRel(CartographyRelSchema):
    "Represents a `RESOURCE` relationship from `AWSAccount` to `AWSPrincipal`."

    target_node_label: str = "AWSAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {
            "id": PropertyRef("AWS_ID", set_in_kwargs=True),
        }
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: AWSPrincipalServiceAccessToAWSAccountRelProperties = (
        AWSPrincipalServiceAccessToAWSAccountRelProperties()
    )


@dataclass(frozen=True)
class AWSPrincipalServiceAccessSchema(CartographyNodeSchema):
    """
    Composite schema that adds service access properties to AWSPrincipal nodes.
    Uses the same label as existing AWSUser/AWSRole/AWSGroup to merge properties.
    """

    label: str = "AWSPrincipal"
    properties: AWSPrincipalServiceAccessNodeProperties = (
        AWSPrincipalServiceAccessNodeProperties()
    )
    sub_resource_relationship: AWSPrincipalServiceAccessToAWSAccountRel = (
        AWSPrincipalServiceAccessToAWSAccountRel()
    )

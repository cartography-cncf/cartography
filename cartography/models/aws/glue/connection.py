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
class GlueConnectionNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "Name", description="The name of the Glue connection definition"
    )
    arn: PropertyRef = PropertyRef(
        "Name",
        extra_index=True,
        description="The name of the Glue connection definition",
    )
    region: PropertyRef = PropertyRef(
        "Region", set_in_kwargs=True, description="The region of the Glue Connection"
    )
    description: PropertyRef = PropertyRef(
        "Description", description="The description of the connection"
    )
    connection_type: PropertyRef = PropertyRef(
        "ConnectionType",
        description="The type of the connection. Currently, SFTP is not supported",
    )
    status: PropertyRef = PropertyRef(
        "Status",
        description="The status of the connection. Can be one of: READY, IN_PROGRESS, or FAILED",
    )
    status_reason: PropertyRef = PropertyRef(
        "StatusReason", description="The reason for the connection status"
    )
    authentication_type: PropertyRef = PropertyRef(
        "AuthenticationType",
        description="A structure containing the authentication configuration",
    )
    secret_arn: PropertyRef = PropertyRef(
        "SecretArn", description="The secret manager ARN to store credentials"
    )
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last time the node was updated",
    )


@dataclass(frozen=True)
class GlueConnectionToAwsAccountRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class GlueConnectionToAWSAccountRel(CartographyRelSchema):
    "Represents a `RESOURCE` relationship from `AWSAccount` to `AWSGlueConnection`."

    target_node_label: str = "AWSAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("AWS_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: GlueConnectionToAwsAccountRelProperties = (
        GlueConnectionToAwsAccountRelProperties()
    )


@dataclass(frozen=True)
class GlueConnectionSchema(CartographyNodeSchema):
    "Represents an `AWSGlueConnection` node in the AWS graph."

    label: str = "AWSGlueConnection"
    # DEPRECATED: legacy GlueConnection node label will be removed in v1.0.0.
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(["GlueConnection"])
    properties: GlueConnectionNodeProperties = GlueConnectionNodeProperties()
    sub_resource_relationship: GlueConnectionToAWSAccountRel = (
        GlueConnectionToAWSAccountRel()
    )

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
class APIGatewayRestAPINodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "id", extra_index=True, description="The id of the REST API"
    )
    createddate: PropertyRef = PropertyRef(
        "createdDate", description="The timestamp when the REST API was created"
    )
    version: PropertyRef = PropertyRef(
        "version", description="The version identifier for the API"
    )
    minimumcompressionsize: PropertyRef = PropertyRef(
        "minimumCompressionSize",
        description="A nullable integer that is used to enable or disable the compression of the REST API",
    )
    disableexecuteapiendpoint: PropertyRef = PropertyRef(
        "disableExecuteApiEndpoint",
        description="Specifies whether clients can invoke your API by using the default `execute-api` endpoint",
    )
    region: PropertyRef = PropertyRef(
        "region",
        set_in_kwargs=True,
        description="The region where the REST API is created",
    )
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last time the node was updated",
    )
    # Policy-level access: True if resource policy allows anonymous/public access
    anonymous_access: PropertyRef = PropertyRef(
        "anonymous_access",
        description="True if this API has a resource policy that allows anonymous/public access (policy-level analysis via PolicyUniverse).",
    )
    anonymous_actions: PropertyRef = PropertyRef(
        "anonymous_actions",
        description="List of anonymous internet accessible actions that may be run on the API (policy-level).",
    )
    # Network-level exposure: Based on endpoint configuration type
    # EDGE/REGIONAL = internet exposed, PRIVATE = VPC only
    endpoint_type: PropertyRef = PropertyRef(
        "endpoint_type",
        extra_index=True,
        description="The endpoint configuration type: `EDGE` (CloudFront), `REGIONAL` (direct), or `PRIVATE` (VPC-only).",
    )
    exposed_internet: PropertyRef = PropertyRef(
        "exposed_internet",
        extra_index=True,
        description="True if the API is network-reachable from the internet (`EDGE` or `REGIONAL`), false for `PRIVATE` endpoints.",
    )


@dataclass(frozen=True)
class APIGatewayRestAPIToAWSAccountRelRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:AWSAPIGatewayRestAPI)<-[:RESOURCE]-(:AWSAccount)
class APIGatewayRestAPIToAWSAccountRel(CartographyRelSchema):
    "Represents a `RESOURCE` relationship from `AWSAccount` to `AWSAPIGatewayRestAPI`."

    target_node_label: str = "AWSAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("AWS_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: APIGatewayRestAPIToAWSAccountRelRelProperties = (
        APIGatewayRestAPIToAWSAccountRelRelProperties()
    )


@dataclass(frozen=True)
class APIGatewayRestAPISchema(CartographyNodeSchema):
    "Represents an `AWSAPIGatewayRestAPI` node in the AWS graph."

    label: str = "AWSAPIGatewayRestAPI"
    # DEPRECATED: legacy APIGatewayRestAPI node label will be removed in v1.0.0.
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(["APIGatewayRestAPI"])
    properties: APIGatewayRestAPINodeProperties = APIGatewayRestAPINodeProperties()
    sub_resource_relationship: APIGatewayRestAPIToAWSAccountRel = (
        APIGatewayRestAPIToAWSAccountRel()
    )

from dataclasses import dataclass

from cartography.models.aws.apigatewayresource import APIGatewayResourceSchema
from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.relationships import CartographyRelProperties
from cartography.models.core.relationships import CartographyRelSchema
from cartography.models.core.relationships import LinkDirection
from cartography.models.core.relationships import make_target_node_matcher
from cartography.models.core.relationships import OtherRelationships
from cartography.models.core.relationships import TargetNodeMatcher


@dataclass(frozen=True)
class APIGatewayMethodProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id")
    api_key_required: PropertyRef = PropertyRef("api_key_required")
    authorization_scopes: PropertyRef = PropertyRef("authorization_scopes")
    authorization_type: PropertyRef = PropertyRef("authorization_type")
    authorizer_id: PropertyRef = PropertyRef("authorizerId")
    http_method: PropertyRef = PropertyRef("http_method")
    operation_name: PropertyRef = PropertyRef("operation_name")
    request_validator_id: PropertyRef = PropertyRef("request_validator_id")
    method_integration_json: PropertyRef = PropertyRef("method_integration_json")
    method_responses_json: PropertyRef = PropertyRef("method_responses_json")
    request_models_json: PropertyRef = PropertyRef("request_models_json")
    request_parameters_json: PropertyRef = PropertyRef("request_parameters_json")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    AWS_ID: PropertyRef = PropertyRef("AWS_ID", set_in_kwargs=True)
    rest_api_id: PropertyRef = PropertyRef("rest_api_id", set_in_kwargs=True)
    resource_id: PropertyRef = PropertyRef("resource_id", set_in_kwargs=True)
    lambda_function_arn: PropertyRef = PropertyRef("lambda_function_arn")
    s3_bucket_name: PropertyRef = PropertyRef("s3_bucket_name")
    dynamodb_table_arn: PropertyRef = PropertyRef("dynamodb_table_arn")


@dataclass(frozen=True)
class APIGatewayMethodToAWSAccountRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class APIGatewayResourceHasMethodRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class APIGatewayMethodInvokesLambdaRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class APIGatewayMethodAccessesServiceRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


# (:AWSAccount)-[:RESOURCE]->(:APIGatewayMethod)
@dataclass(frozen=True)
class APIGatewayMethodToAWSAccountRel(CartographyRelSchema):
    target_node_label: str = "AWSAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {
            "id": PropertyRef("AWS_ID", set_in_kwargs=True),
        }
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: APIGatewayMethodToAWSAccountRelProperties = (
        APIGatewayMethodToAWSAccountRelProperties()
    )


# (:APIGatewayResource)-[HAS]->(:APIGatewayMethod)
class APIGatewayResourceHasMethodRel(CartographyRelSchema):
    target_node_label: str = APIGatewayResourceSchema.label
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {
            "id": PropertyRef("resource_id", set_in_kwargs=True),
        }
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "HAS"
    properties: APIGatewayResourceHasMethodRelProperties = (
        APIGatewayResourceHasMethodRelProperties()
    )


# (:APIGatewayMethod)-[INVOKES]->(:AWSLambda)
@dataclass(frozen=True)
class APIGatewayMethodInvokesLambdaRel(CartographyRelSchema):

    target_node_label: str = "AWSLambda"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {
            "id": PropertyRef("lambda_function_arn", set_in_kwargs=False),
        }
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "INVOKES"
    properties: APIGatewayMethodInvokesLambdaRelProperties = (
        APIGatewayMethodInvokesLambdaRelProperties()
    )


# (:APIGatewayMethod)-[ACCESSES]->(:S3Bucket)
@dataclass(frozen=True)
class APIGatewayMethodAccessesS3Rel(CartographyRelSchema):

    target_node_label: str = "S3Bucket"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {
            "id": PropertyRef("s3_bucket_name", set_in_kwargs=False),
        }
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "ACCESSES"
    properties: APIGatewayMethodAccessesServiceRelProperties = (
        APIGatewayMethodAccessesServiceRelProperties()
    )


# (:APIGatewayMethod)-[ACCESSES]->(:DynamoDBTable)
@dataclass(frozen=True)
class APIGatewayMethodAccessesDynamoDBRel(CartographyRelSchema):
    target_node_label: str = "DynamoDBTable"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {
            "id": PropertyRef("dynamodb_table_arn", set_in_kwargs=False),
        }
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "ACCESSES"
    properties: APIGatewayMethodAccessesServiceRelProperties = (
        APIGatewayMethodAccessesServiceRelProperties()
    )


@dataclass(frozen=True)
class APIGatewayMethodSchema(CartographyNodeSchema):
    label: str = "APIGatewayMethod"
    properties: APIGatewayMethodProperties = APIGatewayMethodProperties()
    sub_resource_relationship: APIGatewayMethodToAWSAccountRel = (
        APIGatewayMethodToAWSAccountRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            APIGatewayResourceHasMethodRel(),
            APIGatewayMethodInvokesLambdaRel(),
            APIGatewayMethodAccessesS3Rel(),
            APIGatewayMethodAccessesDynamoDBRel(),
        ],
    )

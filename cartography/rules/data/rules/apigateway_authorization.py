"""
AWS API Gateway REST API authorization coverage

Methods whose authorization_type is NONE, the API-level roll-up of that, and
REST APIs whose resource policy grants anonymous execute-api access.

Method-level evidence only: an API-level default authorizer is not modelled,
so a method recorded as NONE under one can be a false positive. REST APIs only
- HTTP APIs (v2) carry no method-level authorizer node in the graph.

No collector change is required: every property and relationship used
here is synced by the existing API Gateway module. All rules are
EXPERIMENTAL until validated against a live graph.
"""

from cartography.rules.spec.model import Fact
from cartography.rules.spec.model import Finding
from cartography.rules.spec.model import Maturity
from cartography.rules.spec.model import Module
from cartography.rules.spec.model import Rule


class AwsApigatewayMethodsAuthorizedOutput(Finding):
    account_id: str | None = None
    account: str | None = None
    method_id: str | None = None
    api_id: str | None = None
    resource_id: str | None = None
    http_method: str | None = None
    authorization_type: str | None = None
    authorizer_id: str | None = None


_aws_apigateway_methods_authorized_fact = Fact(
    id="aws_apigateway_methods_authorized_fact",
    name="API method without authorizer",
    description="Methods with authorization_type NONE.",
    cypher_query="""
        MATCH (a:AWSAccount)-[:RESOURCE]->(m:AWSAPIGatewayMethod)
        WHERE m.authorization_type = 'NONE'
        RETURN a.id AS account_id, a.name AS account, m.id AS method_id,
               m.api_id AS api_id, m.resource_id AS resource_id,
               m.httpmethod AS http_method, m.authorization_type AS authorization_type,
               m.authorizer_id AS authorizer_id

    """,
    cypher_visual_query="""
        MATCH (a:AWSAccount)-[:RESOURCE]->(m:AWSAPIGatewayMethod)
        WHERE m.authorization_type = 'NONE'
        RETURN a.id AS account_id, a.name AS account, m.id AS method_id,
               m.api_id AS api_id, m.resource_id AS resource_id,
               m.httpmethod AS http_method, m.authorization_type AS authorization_type,
               m.authorizer_id AS authorizer_id

    """,
    cypher_count_query="""
        MATCH (a:AWSAccount)-[:RESOURCE]->(m:AWSAPIGatewayMethod)
        WHERE m.authorization_type = 'NONE'
        RETURN a.id AS account_id, a.name AS account, m.id AS method_id,
               m.api_id AS api_id, m.resource_id AS resource_id,
               m.httpmethod AS http_method, m.authorization_type AS authorization_type,
               m.authorizer_id AS authorizer_id

    """,
    asset_label="AWSAPIGatewayMethod",
    asset_id_field="method_id",
    identity_fields=("account_id", "account", "method_id"),
    module=Module.AWS,
    maturity=Maturity.EXPERIMENTAL,
)


aws_apigateway_methods_authorized = Rule(
    id="aws_apigateway_methods_authorized",
    name="API Gateway Methods Authorized",
    description="REST API method has authorization_type='NONE' (no authorizer attached). Method-level evidence only: API-level default authorizers are not modeled in cartography, so a method marked NONE under an API-level authorizer may be a false positive.",
    output_model=AwsApigatewayMethodsAuthorizedOutput,
    facts=(_aws_apigateway_methods_authorized_fact,),
    tags=("security", "apigateway", "authentication", "cspm"),
    version="0.1.0",
)


class AwsApigatewayPublicApiAuthorizedOutput(Finding):
    account_id: str | None = None
    account: str | None = None
    api_id: str | None = None
    endpoint_type: str | None = None


_aws_apigateway_public_api_authorized_fact = Fact(
    id="aws_apigateway_public_api_authorized_fact",
    name="Public API with unauthenticated method",
    description="Public REST APIs having any NONE-authorized method.",
    cypher_query="""
        MATCH (a:AWSAccount)-[:RESOURCE]->(api:AWSAPIGatewayRestAPI)
        WHERE api.endpoint_type IN ['EDGE', 'REGIONAL']
        MATCH (api)-[:RESOURCE]->(res:AWSAPIGatewayResource)-[:HAS_METHOD]->(m:AWSAPIGatewayMethod)
        WHERE m.authorization_type = 'NONE'
        RETURN DISTINCT a.id AS account_id, a.name AS account, api.id AS api_id,
               api.endpoint_type AS endpoint_type

    """,
    cypher_visual_query="""
        MATCH (a:AWSAccount)-[:RESOURCE]->(api:AWSAPIGatewayRestAPI)
        WHERE api.endpoint_type IN ['EDGE', 'REGIONAL']
        MATCH (api)-[:RESOURCE]->(res:AWSAPIGatewayResource)-[:HAS_METHOD]->(m:AWSAPIGatewayMethod)
        WHERE m.authorization_type = 'NONE'
        RETURN DISTINCT a.id AS account_id, a.name AS account, api.id AS api_id,
               api.endpoint_type AS endpoint_type

    """,
    cypher_count_query="""
        MATCH (a:AWSAccount)-[:RESOURCE]->(api:AWSAPIGatewayRestAPI)
        WHERE api.endpoint_type IN ['EDGE', 'REGIONAL']
        MATCH (api)-[:RESOURCE]->(res:AWSAPIGatewayResource)-[:HAS_METHOD]->(m:AWSAPIGatewayMethod)
        WHERE m.authorization_type = 'NONE'
        RETURN DISTINCT a.id AS account_id, a.name AS account, api.id AS api_id,
               api.endpoint_type AS endpoint_type

    """,
    asset_label="AWSAPIGatewayRestAPI",
    asset_id_field="api_id",
    identity_fields=("account_id", "account", "api_id"),
    module=Module.AWS,
    maturity=Maturity.EXPERIMENTAL,
)


aws_apigateway_public_api_authorized = Rule(
    id="aws_apigateway_public_api_authorized",
    name="API Gateway Public API Authorized",
    description="Public (EDGE/REGIONAL) REST API has at least one method without an authorizer (authorization_type='NONE'), traversed via API-[:RESOURCE]->resource-[:HAS_METHOD]->method. One finding per API (DISTINCT). Method-level evidence only: API-level default authorizers are not modeled. Count denominator: public (EDGE/REGIONAL) REST APIs.",
    output_model=AwsApigatewayPublicApiAuthorizedOutput,
    facts=(_aws_apigateway_public_api_authorized_fact,),
    tags=("security", "apigateway", "authentication", "attack_surface", "cspm"),
    version="0.1.0",
)


class AwsApigatewayRestapiResourcePolicyPublicOutput(Finding):
    account_id: str | None = None
    account: str | None = None
    api_id: str | None = None
    endpoint_type: str | None = None
    anonymous_actions: str | None = None
    region: str | None = None


_aws_apigateway_restapi_resource_policy_public_fact = Fact(
    id="aws_apigateway_restapi_resource_policy_public_fact",
    name="REST API with anonymous resource-policy access",
    description="REST APIs whose resource policy is internet-accessible.",
    cypher_query="""
        MATCH (a:AWSAccount)-[:RESOURCE]->(api:AWSAPIGatewayRestAPI)
        WHERE api.anonymous_access = true
        RETURN a.id AS account_id, a.name AS account, api.id AS api_id,
               api.endpoint_type AS endpoint_type,
               api.anonymous_actions AS anonymous_actions, api.region AS region

    """,
    cypher_visual_query="""
        MATCH (a:AWSAccount)-[:RESOURCE]->(api:AWSAPIGatewayRestAPI)
        WHERE api.anonymous_access = true
        RETURN a.id AS account_id, a.name AS account, api.id AS api_id,
               api.endpoint_type AS endpoint_type,
               api.anonymous_actions AS anonymous_actions, api.region AS region

    """,
    cypher_count_query="""
        MATCH (a:AWSAccount)-[:RESOURCE]->(api:AWSAPIGatewayRestAPI)
        WHERE api.anonymous_access = true
        RETURN a.id AS account_id, a.name AS account, api.id AS api_id,
               api.endpoint_type AS endpoint_type,
               api.anonymous_actions AS anonymous_actions, api.region AS region

    """,
    asset_label="AWSAPIGatewayRestAPI",
    asset_id_field="api_id",
    identity_fields=("account_id", "api_id"),
    module=Module.AWS,
    maturity=Maturity.EXPERIMENTAL,
)


aws_apigateway_restapi_resource_policy_public = Rule(
    id="aws_apigateway_restapi_resource_policy_public",
    name="API Gateway REST API Public Resource Policy",
    description="A REST API whose resource policy grants anonymous (public) execute-api access; anonymous_actions lists the internet-accessible actions parsed from the policy. Complements the method-level authorization check aws_apigateway_methods_authorized.",
    output_model=AwsApigatewayRestapiResourcePolicyPublicOutput,
    facts=(_aws_apigateway_restapi_resource_policy_public_fact,),
    tags=("security", "apigateway", "perimeter"),
    version="0.1.0",
)

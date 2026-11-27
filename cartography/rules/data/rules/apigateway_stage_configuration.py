"""
AWS API Gateway stage protection, tracing and backend mutual TLS

Stages with no WAF web ACL, stages with X-Ray tracing off, and stages with no
client certificate for backend mutual TLS.

webaclarn is only populated when a WAFv2 web ACL is associated with the stage;
WAF Classic associations are not modelled, so a stage protected by a Classic
ACL reads as unprotected. The client-certificate check applies to REST API
integrations that authenticate to the backend, not to HTTP proxy integrations
that do not, so it over-reports on those.

No collector change is required: every property and relationship used
here is synced by the existing API Gateway module. All rules are
EXPERIMENTAL until validated against a live graph.
"""

from cartography.rules.spec.model import Fact
from cartography.rules.spec.model import Finding
from cartography.rules.spec.model import Maturity
from cartography.rules.spec.model import Module
from cartography.rules.spec.model import Rule


class AwsApigatewayStageClientCertificateOutput(Finding):
    account_id: str | None = None
    account: str | None = None
    stage_id: str | None = None
    stage_name: str | None = None
    client_certificate_id: str | None = None


_aws_apigateway_stage_client_certificate_fact = Fact(
    id="aws_apigateway_stage_client_certificate_fact",
    name="Stage without client certificate",
    description="Stages with null/empty clientcertificateid.",
    cypher_query="""
        MATCH (a:AWSAccount)-[:RESOURCE]->(s:AWSAPIGatewayStage)
        WHERE s.clientcertificateid IS NULL OR s.clientcertificateid = ''
        RETURN a.id AS account_id, a.name AS account, s.id AS stage_id,
               s.stagename AS stage_name, s.clientcertificateid AS client_certificate_id

    """,
    cypher_visual_query="""
        MATCH (a:AWSAccount)-[:RESOURCE]->(s:AWSAPIGatewayStage)
        WHERE s.clientcertificateid IS NULL OR s.clientcertificateid = ''
        RETURN a.id AS account_id, a.name AS account, s.id AS stage_id,
               s.stagename AS stage_name, s.clientcertificateid AS client_certificate_id

    """,
    cypher_count_query="""
        MATCH (a:AWSAccount)-[:RESOURCE]->(s:AWSAPIGatewayStage)
        WHERE s.clientcertificateid IS NULL OR s.clientcertificateid = ''
        RETURN a.id AS account_id, a.name AS account, s.id AS stage_id,
               s.stagename AS stage_name, s.clientcertificateid AS client_certificate_id

    """,
    asset_label="AWSAPIGatewayStage",
    asset_id_field="stage_id",
    identity_fields=("account_id", "account", "stage_id"),
    module=Module.AWS,
    maturity=Maturity.EXPERIMENTAL,
)


aws_apigateway_stage_client_certificate = Rule(
    id="aws_apigateway_stage_client_certificate",
    name="API Gateway Stage Client Certificate",
    description="REST API stage has no client certificate configured (clientcertificateid null/empty), so API Gateway cannot mutual-TLS authenticate to the backend.",
    output_model=AwsApigatewayStageClientCertificateOutput,
    facts=(_aws_apigateway_stage_client_certificate_fact,),
    tags=("security", "apigateway", "encryption", "cspm"),
    version="0.1.0",
)


class AwsApigatewayStageWafAttachedOutput(Finding):
    account_id: str | None = None
    account: str | None = None
    stage_id: str | None = None
    stage_name: str | None = None
    web_acl_arn: str | None = None


_aws_apigateway_stage_waf_attached_fact = Fact(
    id="aws_apigateway_stage_waf_attached_fact",
    name="Stage without WAF ACL",
    description="Stages with null/empty webaclarn.",
    cypher_query="""
        MATCH (a:AWSAccount)-[:RESOURCE]->(s:AWSAPIGatewayStage)
        WHERE s.webaclarn IS NULL OR s.webaclarn = ''
        RETURN a.id AS account_id, a.name AS account, s.id AS stage_id,
               s.stagename AS stage_name, s.webaclarn AS web_acl_arn

    """,
    cypher_visual_query="""
        MATCH (a:AWSAccount)-[:RESOURCE]->(s:AWSAPIGatewayStage)
        WHERE s.webaclarn IS NULL OR s.webaclarn = ''
        RETURN a.id AS account_id, a.name AS account, s.id AS stage_id,
               s.stagename AS stage_name, s.webaclarn AS web_acl_arn

    """,
    cypher_count_query="""
        MATCH (a:AWSAccount)-[:RESOURCE]->(s:AWSAPIGatewayStage)
        WHERE s.webaclarn IS NULL OR s.webaclarn = ''
        RETURN a.id AS account_id, a.name AS account, s.id AS stage_id,
               s.stagename AS stage_name, s.webaclarn AS web_acl_arn

    """,
    asset_label="AWSAPIGatewayStage",
    asset_id_field="stage_id",
    identity_fields=("account_id", "account", "stage_id"),
    module=Module.AWS,
    maturity=Maturity.EXPERIMENTAL,
)


aws_apigateway_stage_waf_attached = Rule(
    id="aws_apigateway_stage_waf_attached",
    name="API Gateway Stage WAF Attached",
    description="REST API stage has no WAF web ACL attached (webaclarn null/empty).",
    output_model=AwsApigatewayStageWafAttachedOutput,
    facts=(_aws_apigateway_stage_waf_attached_fact,),
    tags=("security", "apigateway", "waf", "cspm"),
    version="0.1.0",
)


class AwsApigatewayStageXrayTracingOutput(Finding):
    account_id: str | None = None
    account: str | None = None
    stage_arn: str | None = None
    stage_name: str | None = None
    rest_api_id: str | None = None
    tracing_enabled: bool | None = None


_aws_apigateway_stage_xray_tracing_fact = Fact(
    id="aws_apigateway_stage_xray_tracing_fact",
    name="API Gateway stage without tracing",
    description="Stages whose tracingenabled is false or unset.",
    cypher_query="""
        MATCH (a:AWSAccount)-[:RESOURCE]->(s:AWSAPIGatewayStage)
        WHERE s.tracingenabled IS NULL OR s.tracingenabled <> true
        OPTIONAL MATCH (api:AWSAPIGatewayRestAPI)-[:ASSOCIATED_WITH]->(s)
        RETURN a.id AS account_id, a.name AS account, s.id AS stage_arn,
               s.stagename AS stage_name, api.id AS rest_api_id,
               s.tracingenabled AS tracing_enabled

    """,
    cypher_visual_query="""
        MATCH (a:AWSAccount)-[:RESOURCE]->(s:AWSAPIGatewayStage)
        WHERE s.tracingenabled IS NULL OR s.tracingenabled <> true
        OPTIONAL MATCH (api:AWSAPIGatewayRestAPI)-[:ASSOCIATED_WITH]->(s)
        RETURN a.id AS account_id, a.name AS account, s.id AS stage_arn,
               s.stagename AS stage_name, api.id AS rest_api_id,
               s.tracingenabled AS tracing_enabled

    """,
    cypher_count_query="""
        MATCH (a:AWSAccount)-[:RESOURCE]->(s:AWSAPIGatewayStage)
        WHERE s.tracingenabled IS NULL OR s.tracingenabled <> true
        OPTIONAL MATCH (api:AWSAPIGatewayRestAPI)-[:ASSOCIATED_WITH]->(s)
        RETURN a.id AS account_id, a.name AS account, s.id AS stage_arn,
               s.stagename AS stage_name, api.id AS rest_api_id,
               s.tracingenabled AS tracing_enabled

    """,
    asset_label="AWSAPIGatewayStage",
    asset_id_field="stage_arn",
    identity_fields=(
        "account_id",
        "account",
        "stage_arn",
        "rest_api_id",
    ),
    module=Module.AWS,
    maturity=Maturity.EXPERIMENTAL,
)


aws_apigateway_stage_xray_tracing = Rule(
    id="aws_apigateway_stage_xray_tracing",
    name="API Gateway Stage X-Ray Tracing",
    description="API Gateway REST API stage with X-Ray active tracing disabled (tracingenabled not true).",
    output_model=AwsApigatewayStageXrayTracingOutput,
    facts=(_aws_apigateway_stage_xray_tracing_fact,),
    tags=("observability", "apigateway", "logging", "cspm"),
    version="0.1.0",
)

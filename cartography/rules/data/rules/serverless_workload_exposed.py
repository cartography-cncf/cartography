from cartography.rules.spec.model import Fact
from cartography.rules.spec.model import Finding
from cartography.rules.spec.model import Maturity
from cartography.rules.spec.model import Module
from cartography.rules.spec.model import Rule

# GCP Facts
_gcp_cloud_run_public_ingress = Fact(
    id="gcp_cloud_run_public_ingress",
    name="Internet-Accessible Cloud Run Service Attack Surface",
    description=(
        "Cloud Run services that allow ingress from the public internet "
        "(ingress = INGRESS_TRAFFIC_ALL) AND grant roles/run.invoker to "
        "allUsers or allAuthenticatedUsers via an unconditional IAM binding. "
        "Both layers must be permissive for the service to be anonymously "
        "invokable from the internet."
    ),
    cypher_query="""
    MATCH (svc:GCPCloudRunService)
    WHERE svc.ingress = 'INGRESS_TRAFFIC_ALL'
      AND EXISTS {
          MATCH (svc)<-[:APPLIES_TO]-(binding:GCPPolicyBinding)
          WHERE binding.is_public = true
            AND coalesce(binding.has_condition, false) = false
            AND binding.role = 'roles/run.invoker'
      }
    RETURN
        svc.id AS id,
        svc.name AS name,
        svc.location AS region,
        'cloud_run_public_ingress' AS exposure_type
    """,
    cypher_visual_query="""
    MATCH p=(svc:GCPCloudRunService)<-[:APPLIES_TO]-(binding:GCPPolicyBinding)
    WHERE svc.ingress = 'INGRESS_TRAFFIC_ALL'
      AND binding.is_public = true
      AND coalesce(binding.has_condition, false) = false
      AND binding.role = 'roles/run.invoker'
    RETURN *
    """,
    cypher_count_query="""
    MATCH (svc:GCPCloudRunService)
    RETURN COUNT(svc) AS count
    """,
    asset_id_field="id",
    module=Module.GCP,
    maturity=Maturity.EXPERIMENTAL,
)


_gcp_cloud_function_http_trigger = Fact(
    id="gcp_cloud_function_http_trigger",
    name="Internet-Accessible Cloud Function Attack Surface",
    description=(
        "Cloud Functions configured with an HTTPS trigger AND granting "
        "an invoker role (roles/cloudfunctions.invoker for 1st gen, "
        "roles/run.invoker for 2nd gen, which runs on Cloud Run) to "
        "allUsers or allAuthenticatedUsers via an unconditional IAM "
        "binding. Anonymous callers can invoke the function over the "
        "public internet."
    ),
    cypher_query="""
    MATCH (fn:GCPCloudFunction)
    WHERE fn.https_trigger_url IS NOT NULL
      AND EXISTS {
          MATCH (fn)<-[:APPLIES_TO]-(binding:GCPPolicyBinding)
          WHERE binding.is_public = true
            AND coalesce(binding.has_condition, false) = false
            AND binding.role IN [
                'roles/cloudfunctions.invoker',
                'roles/run.invoker'
            ]
      }
    RETURN
        fn.id AS id,
        fn.name AS name,
        fn.region AS region,
        fn.runtime AS runtime,
        'cloud_function_http_trigger' AS exposure_type
    """,
    cypher_visual_query="""
    MATCH p=(fn:GCPCloudFunction)<-[:APPLIES_TO]-(binding:GCPPolicyBinding)
    WHERE fn.https_trigger_url IS NOT NULL
      AND binding.is_public = true
      AND coalesce(binding.has_condition, false) = false
      AND binding.role IN [
          'roles/cloudfunctions.invoker',
          'roles/run.invoker'
      ]
    RETURN *
    """,
    cypher_count_query="""
    MATCH (fn:GCPCloudFunction)
    RETURN COUNT(fn) AS count
    """,
    asset_id_field="id",
    module=Module.GCP,
    maturity=Maturity.EXPERIMENTAL,
)


# AWS Facts
_aws_lambda_anonymous_access = Fact(
    id="aws_lambda_anonymous_access",
    name="Internet-Accessible AWS Lambda Attack Surface",
    description=(
        "AWS Lambda functions whose resource policy allows anonymous "
        "invocation. The cartography AWS Lambda intel module sets "
        "anonymous_access = true when the function's resource-based policy "
        "grants the lambda:InvokeFunction action (or equivalent) to a "
        "wildcard principal, which covers Function URLs configured with "
        "AuthType=NONE as well as policies opened to '*' / Everyone."
    ),
    cypher_query="""
    MATCH (acc:AWSAccount)-[:RESOURCE]->(fn:AWSLambda)
    WHERE fn.anonymous_access = true
    RETURN
        fn.arn AS id,
        fn.name AS name,
        fn.region AS region,
        fn.runtime AS runtime,
        'lambda_anonymous_invoke' AS exposure_type
    """,
    cypher_visual_query="""
    MATCH p=(acc:AWSAccount)-[:RESOURCE]->(fn:AWSLambda)
    WHERE fn.anonymous_access = true
    RETURN *
    """,
    cypher_count_query="""
    MATCH (fn:AWSLambda)
    RETURN COUNT(fn) AS count
    """,
    asset_id_field="id",
    module=Module.AWS,
    maturity=Maturity.EXPERIMENTAL,
)


# TODO: add an Azure Function App fact once the cartography intel module
# ingests siteConfig.publicNetworkAccess and privateEndpointConnections.
# Today only `https_only` and `state` are modelled, which is not enough to
# discriminate publicly-invokable Function Apps from privately-bound ones.


# Rule
class ServerlessWorkloadExposed(Finding):
    id: str | None = None
    name: str | None = None
    region: str | None = None
    runtime: str | None = None
    exposure_type: str | None = None


serverless_workload_exposed = Rule(
    id="serverless_workload_exposed",
    name="Internet-Exposed Serverless Workloads",
    description=(
        "Serverless compute reachable from the public internet via "
        "permissive ingress, anonymous IAM bindings, or unauthenticated "
        "Function URLs. Covers GCP Cloud Run, GCP Cloud Functions, and "
        "AWS Lambda."
    ),
    output_model=ServerlessWorkloadExposed,
    facts=(
        _aws_lambda_anonymous_access,
        _gcp_cloud_run_public_ingress,
        _gcp_cloud_function_http_trigger,
    ),
    tags=(
        "infrastructure",
        "serverless",
        "attack_surface",
        "stride:tampering",
        "stride:elevation_of_privilege",
    ),
    version="0.1.0",
)

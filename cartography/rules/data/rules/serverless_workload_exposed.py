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
        "(ingress = INGRESS_TRAFFIC_ALL) AND grant the run.invoker role to "
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
        "Cloud Functions configured with an HTTPS trigger AND granting the "
        "cloudfunctions.invoker role (or equivalent) to allUsers or "
        "allAuthenticatedUsers via an unconditional IAM binding. Anonymous "
        "callers can invoke the function over the public internet."
    ),
    cypher_query="""
    MATCH (fn:GCPCloudFunction)
    WHERE fn.https_trigger_url IS NOT NULL
      AND EXISTS {
          MATCH (fn)<-[:APPLIES_TO]-(binding:GCPPolicyBinding)
          WHERE binding.is_public = true
            AND coalesce(binding.has_condition, false) = false
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
        "permissive ingress or anonymous IAM bindings. Covers GCP Cloud "
        "Run and GCP Cloud Functions."
    ),
    output_model=ServerlessWorkloadExposed,
    facts=(
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

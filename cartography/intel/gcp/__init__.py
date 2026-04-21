import json
import logging
from collections import namedtuple
from typing import Any
from typing import Callable
from typing import cast
from typing import Dict
from typing import List
from typing import Optional
from typing import Set

import neo4j
from google.auth.credentials import Credentials as GoogleCredentials
from google.cloud.asset_v1 import AssetServiceClient
from googleapiclient.discovery import HttpError
from googleapiclient.discovery import Resource

from cartography.config import Config
from cartography.graph.job import GraphJob
from cartography.intel.gcp import artifact_registry
from cartography.intel.gcp import bigquery_connection
from cartography.intel.gcp import bigquery_dataset
from cartography.intel.gcp import bigquery_routine
from cartography.intel.gcp import bigquery_table
from cartography.intel.gcp import bigtable_app_profile
from cartography.intel.gcp import bigtable_backup
from cartography.intel.gcp import bigtable_cluster
from cartography.intel.gcp import bigtable_instance
from cartography.intel.gcp import bigtable_table
from cartography.intel.gcp import cai
from cartography.intel.gcp import cloud_sql_backup_config
from cartography.intel.gcp import cloud_sql_database
from cartography.intel.gcp import cloud_sql_instance
from cartography.intel.gcp import cloud_sql_user
from cartography.intel.gcp import compute
from cartography.intel.gcp import dns
from cartography.intel.gcp import gcf
from cartography.intel.gcp import gke
from cartography.intel.gcp import iam
from cartography.intel.gcp import kms
from cartography.intel.gcp import permission_relationships
from cartography.intel.gcp import policy_bindings
from cartography.intel.gcp import secretsmanager
from cartography.intel.gcp import storage
from cartography.intel.gcp.clients import build_asset_client
from cartography.intel.gcp.clients import build_bigquery_client
from cartography.intel.gcp.clients import build_bigquery_connection_client
from cartography.intel.gcp.clients import build_client
from cartography.intel.gcp.clients import build_cloud_run_clients
from cartography.intel.gcp.clients import CloudRunClients
from cartography.intel.gcp.clients import get_gcp_credentials
from cartography.intel.gcp.cloudrun import execution as cloudrun_execution
from cartography.intel.gcp.cloudrun import job as cloudrun_job
from cartography.intel.gcp.cloudrun import revision as cloudrun_revision
from cartography.intel.gcp.cloudrun import service as cloudrun_service
from cartography.intel.gcp.cloudrun import util as cloudrun_util
from cartography.intel.gcp.crm.folders import sync_gcp_folders
from cartography.intel.gcp.crm.orgs import sync_gcp_organizations
from cartography.intel.gcp.crm.projects import sync_gcp_projects
from cartography.intel.gcp.util import parse_and_validate_gcp_requested_syncs
from cartography.intel.gcp.vertex.datasets import sync_vertex_ai_datasets
from cartography.intel.gcp.vertex.deployed_models import sync_vertex_ai_deployed_models
from cartography.intel.gcp.vertex.endpoints import sync_vertex_ai_endpoints
from cartography.intel.gcp.vertex.feature_groups import sync_feature_groups
from cartography.intel.gcp.vertex.instances import sync_workbench_instances
from cartography.intel.gcp.vertex.models import sync_vertex_ai_models
from cartography.intel.gcp.vertex.training_pipelines import sync_training_pipelines
from cartography.models.gcp.crm.folders import GCPFolderSchema
from cartography.models.gcp.crm.organizations import GCPOrganizationSchema
from cartography.models.gcp.crm.projects import GCPProjectSchema
from cartography.util import run_analysis_job
from cartography.util import run_scoped_analysis_job
from cartography.util import timeit

logger = logging.getLogger(__name__)

_ClientCache = dict[tuple[str, str], Any]

# Mapping of service short names to their full names as in docs. See https://developers.google.com/apis-explorer,
# and https://cloud.google.com/service-usage/docs/reference/rest/v1/services#ServiceConfig
Services = namedtuple(
    "Services",
    "compute storage gke dns iam kms bigtable cai aiplatform cloud_sql gcf secretsmanager artifact_registry cloud_run bigquery bigquery_connection",
)
service_names = Services(
    compute="compute.googleapis.com",
    storage="storage.googleapis.com",
    gke="container.googleapis.com",
    dns="dns.googleapis.com",
    iam="iam.googleapis.com",
    kms="cloudkms.googleapis.com",
    bigtable="bigtableadmin.googleapis.com",
    cai="cloudasset.googleapis.com",
    aiplatform="aiplatform.googleapis.com",
    cloud_sql="sqladmin.googleapis.com",
    gcf="cloudfunctions.googleapis.com",
    secretsmanager="secretmanager.googleapis.com",
    artifact_registry="artifactregistry.googleapis.com",
    cloud_run="run.googleapis.com",
    bigquery="bigquery.googleapis.com",
    bigquery_connection="bigqueryconnection.googleapis.com",
)


def _services_enabled_on_project(serviceusage: Resource, project_id: str) -> Set:
    """
    Return a list of all Google API services that are enabled on the given project ID.
    See https://cloud.google.com/service-usage/docs/reference/rest/v1/services/list for data shape.
    :param serviceusage: the serviceusage resource provider. See https://cloud.google.com/service-usage/docs/overview.
    :param project_id: The project ID number to sync.  See  the `projectId` field in
    https://cloud.google.com/resource-manager/reference/rest/v1/projects
    :return: A set of services that are enabled on the project
    """
    try:
        req = serviceusage.services().list(
            parent=f"projects/{project_id}",
            filter="state:ENABLED",
        )
        services = set()
        while req is not None:
            res = req.execute()
            if "services" in res:
                services.update({svc["config"]["name"] for svc in res["services"]})
            req = serviceusage.services().list_next(
                previous_request=req,
                previous_response=res,
            )
        return services
    except HttpError as http_error:
        http_error = json.loads(http_error.content.decode("utf-8"))
        # This is set to log-level `info` because Google creates many projects under the hood that cartography cannot
        # audit (e.g. adding a script to a Google spreadsheet causes a project to get created) and we don't need to emit
        # a warning for these projects.
        logger.info(
            f"HttpError when trying to get enabled services on project {project_id}. "
            f"Code: {http_error['error']['code']}, Message: {http_error['error']['message']}. "
            f"Skipping.",
        )
        return set()


def _get_cached(
    client_cache: _ClientCache,
    key: tuple[str, str],
    factory: Callable[[], Any],
) -> Any:
    client = client_cache.get(key)
    if client is None:
        client = factory()
        client_cache[key] = client
    return client


def _get_cached_client(
    client_cache: _ClientCache,
    service: str,
    version: str,
    credentials: GoogleCredentials,
) -> Resource:
    return cast(
        Resource,
        _get_cached(
            client_cache,
            (service, version),
            lambda: build_client(service, version, credentials=credentials),
        ),
    )


def _sync_project_resources(
    neo4j_session: neo4j.Session,
    projects: List[Dict],
    gcp_update_tag: int,
    common_job_parameters: Dict,
    credentials: GoogleCredentials,
    client_cache: _ClientCache,
    requested_syncs: Set[str] | None = None,
) -> None:
    """
    Syncs GCP service-specific resources (Compute, Storage, GKE, DNS, IAM) for each project.
    :param neo4j_session: The Neo4j session
    :param projects: A list of projects containing at minimum a "projectId" field.
    :param gcp_update_tag: The timestamp value to set our new Neo4j nodes with
    :param common_job_parameters: Other parameters sent to Neo4j
    :param credentials: GCP credentials to use for API calls.
    :param requested_syncs: Optional set of resource names to sync. If None, all resources are synced.
    :return: Nothing
    """
    logger.info("Syncing resources for %d GCP projects.", len(projects))

    # Cloud Asset Inventory (CAI) clients are lazily initialized and reused across all projects.
    # CAI is used for:
    # 1. Fallback IAM sync when IAM API is disabled on target projects (cai_rest_client)
    # 2. Policy bindings sync (cai_grpc_client)
    #
    # Note: We do NOT explicitly set a quota project for CAI clients. Google's default behavior
    # will use the service account's host project for quota/billing, which doesn't require
    # the serviceusage.serviceUsageConsumer permission.
    cai_rest_client: Optional[Resource] = None  # REST client for asset listing
    cai_grpc_client: Optional[AssetServiceClient] = None  # gRPC client for policy APIs
    serviceusage_client = _get_cached_client(
        client_cache,
        "serviceusage",
        "v1",
        credentials,
    )

    # Per-project sync across services
    for project in projects:
        project_id = project["projectId"]
        common_job_parameters["PROJECT_ID"] = project_id
        project_services = _services_enabled_on_project(serviceusage_client, project_id)

        # If the user specified --gcp-requested-syncs, filter to only include the
        # requested ones. This mirrors the AWS selective sync pattern.
        if requested_syncs is not None:
            requested_service_apis = {
                getattr(service_names, r)
                for r in requested_syncs
                if hasattr(service_names, r)
            }
            enabled_services = project_services & requested_service_apis
        else:
            enabled_services = project_services

        # Track whether IAM sync succeeded for this project.
        # Only run IAM cleanup if sync succeeded to avoid deleting valid data
        # when both IAM API is disabled and CAI fallback fails.
        iam_sync_succeeded = False

        if service_names.compute in enabled_services:
            logger.info("Syncing GCP project %s for Compute.", project_id)
            compute_cred = _get_cached_client(
                client_cache,
                "compute",
                "v1",
                credentials,
            )
            compute.sync(
                neo4j_session,
                compute_cred,
                project_id,
                gcp_update_tag,
                common_job_parameters,
            )

        if service_names.storage in enabled_services:
            logger.info("Syncing GCP project %s for Storage.", project_id)
            storage_cred = _get_cached_client(
                client_cache,
                "storage",
                "v1",
                credentials,
            )
            storage.sync_gcp_buckets(
                neo4j_session,
                storage_cred,
                project_id,
                gcp_update_tag,
                common_job_parameters,
            )

        if service_names.gke in enabled_services:
            logger.info("Syncing GCP project %s for GKE.", project_id)
            container_cred = _get_cached_client(
                client_cache,
                "container",
                "v1",
                credentials,
            )
            gke.sync_gke_clusters(
                neo4j_session,
                container_cred,
                project_id,
                gcp_update_tag,
                common_job_parameters,
            )

        if service_names.dns in enabled_services:
            logger.info("Syncing GCP project %s for DNS.", project_id)
            dns_cred = _get_cached_client(client_cache, "dns", "v1", credentials)
            dns.sync(
                neo4j_session,
                dns_cred,
                project_id,
                gcp_update_tag,
                common_job_parameters,
            )

        if service_names.gcf in enabled_services:
            logger.info("Syncing GCP project %s for Cloud Functions.", project_id)
            gcf_cred = _get_cached_client(
                client_cache,
                "cloudfunctions",
                "v1",
                credentials,
            )
            gcf.sync(
                neo4j_session,
                gcf_cred,
                project_id,
                gcp_update_tag,
                common_job_parameters,
            )

        if service_names.iam in enabled_services:
            logger.info("Syncing GCP project %s for IAM.", project_id)
            iam_cred = _get_cached_client(client_cache, "iam", "v1", credentials)
            iam.sync(
                neo4j_session,
                iam_cred,
                project_id,
                gcp_update_tag,
                common_job_parameters,
            )
            iam_sync_succeeded = True
        if service_names.kms in enabled_services:
            logger.info("Syncing GCP project %s for KMS.", project_id)
            kms_cred = _get_cached_client(
                client_cache,
                "cloudkms",
                "v1",
                credentials,
            )
            kms.sync(
                neo4j_session,
                kms_cred,
                project_id,
                gcp_update_tag,
                common_job_parameters,
            )

        if service_names.iam not in enabled_services and (
            requested_syncs is None or "iam" in requested_syncs
        ):
            # Fallback to Cloud Asset Inventory even if the target project does not have the IAM API enabled.
            # CAI uses the service account's host project for quota by default (no explicit quota project needed).
            # Note: Predefined/org roles are synced at org level via sync_org_iam(); CAI only syncs
            # project-level service accounts and custom roles.
            # Lazily initialize the CAI REST client once and reuse it for all projects.
            if cai_rest_client is None:
                cai_rest_client = _get_cached_client(
                    client_cache,
                    "cloudasset",
                    "v1",
                    credentials,
                )

            logger.info(
                "IAM API not enabled. Attempting IAM sync for project %s via Cloud Asset Inventory.",
                project_id,
            )
            try:
                cai.sync(
                    neo4j_session,
                    cai_rest_client,
                    project_id,
                    gcp_update_tag,
                    common_job_parameters,
                )
                iam_sync_succeeded = True
            except HttpError as e:
                if e.resp.status == 403:
                    logger.warning(
                        "CAI fallback skipped for project %s: %s. "
                        "Ensure Cloud Asset API is enabled and roles/cloudasset.viewer is granted.",
                        project_id,
                        e.reason,
                    )
                    # iam_sync_succeeded stays False - don't run cleanup for this project
                else:
                    raise
        if service_names.bigtable in enabled_services:
            logger.info(f"Syncing GCP project {project_id} for Bigtable.")
            bigtable_client = _get_cached_client(
                client_cache,
                "bigtableadmin",
                "v2",
                credentials,
            )
            instances_raw = bigtable_instance.sync_bigtable_instances(
                neo4j_session,
                bigtable_client,
                project_id,
                gcp_update_tag,
                common_job_parameters,
            )

            if instances_raw is not None:
                clusters_raw = bigtable_cluster.sync_bigtable_clusters(
                    neo4j_session,
                    bigtable_client,
                    instances_raw,
                    project_id,
                    gcp_update_tag,
                    common_job_parameters,
                )

                bigtable_table.sync_bigtable_tables(
                    neo4j_session,
                    bigtable_client,
                    instances_raw,
                    project_id,
                    gcp_update_tag,
                    common_job_parameters,
                )

                bigtable_app_profile.sync_bigtable_app_profiles(
                    neo4j_session,
                    bigtable_client,
                    instances_raw,
                    project_id,
                    gcp_update_tag,
                    common_job_parameters,
                )

                # Always run backup sync when instances_raw is not None.
                # Even if clusters_raw is empty (all instances deleted), we need to
                # run cleanup to remove stale backup nodes.
                bigtable_backup.sync_bigtable_backups(
                    neo4j_session,
                    bigtable_client,
                    clusters_raw,
                    project_id,
                    gcp_update_tag,
                    common_job_parameters,
                )

        if service_names.aiplatform in enabled_services:
            logger.info(f"Syncing GCP project {project_id} for Vertex AI.")
            aiplatform_client = _get_cached_client(
                client_cache,
                "aiplatform",
                "v1",
                credentials,
            )
            sync_vertex_ai_models(
                neo4j_session,
                aiplatform_client,
                project_id,
                gcp_update_tag,
                common_job_parameters,
            )
            endpoints_raw = sync_vertex_ai_endpoints(
                neo4j_session,
                aiplatform_client,
                project_id,
                gcp_update_tag,
                common_job_parameters,
            )
            # Always run deployed models sync when endpoints sync succeeded.
            # Even if endpoints_raw is empty (no endpoints), we need to
            # run cleanup to remove stale deployed model nodes.
            sync_vertex_ai_deployed_models(
                neo4j_session,
                endpoints_raw,
                project_id,
                gcp_update_tag,
                common_job_parameters,
            )
            sync_workbench_instances(
                neo4j_session,
                aiplatform_client,
                project_id,
                gcp_update_tag,
                common_job_parameters,
            )
            sync_training_pipelines(
                neo4j_session,
                aiplatform_client,
                project_id,
                gcp_update_tag,
                common_job_parameters,
            )
            sync_feature_groups(
                neo4j_session,
                aiplatform_client,
                project_id,
                gcp_update_tag,
                common_job_parameters,
            )
            sync_vertex_ai_datasets(
                neo4j_session,
                aiplatform_client,
                project_id,
                gcp_update_tag,
                common_job_parameters,
            )

        # Policy bindings sync uses the CAI gRPC client.
        # CAI enablement is project-specific, so evaluate it for each project
        # instead of caching the first project's state across the whole worker.
        if requested_syncs is None or "policy_bindings" in requested_syncs:
            if service_names.cai not in project_services:
                logger.info(
                    "CAI not enabled on project %s, skipping policy bindings sync. "
                    "Enable the Cloud Asset Inventory API to sync IAM policy bindings.",
                    project_id,
                )
            else:
                # Lazily initialize the CAI gRPC client and reuse it across projects.
                if cai_grpc_client is None:
                    cai_grpc_client = cast(
                        AssetServiceClient,
                        _get_cached(
                            client_cache,
                            ("cloudasset", "grpc"),
                            lambda: build_asset_client(credentials=credentials),
                        ),
                    )
                logger.info(
                    "Syncing IAM policies for GCP project %s.",
                    project_id,
                )
                policy_bindings.sync(
                    neo4j_session,
                    project_id,
                    gcp_update_tag,
                    common_job_parameters,
                    cai_grpc_client,
                )

        if requested_syncs is None or "permission_relationships" in requested_syncs:
            permission_relationships.sync(
                neo4j_session,
                project_id,
                gcp_update_tag,
                common_job_parameters,
            )

        if service_names.cloud_sql in enabled_services:
            logger.info("Syncing GCP project %s for Cloud SQL.", project_id)
            cloud_sql_cred = _get_cached_client(
                client_cache,
                "sqladmin",
                "v1beta4",
                credentials,
            )

            instances_raw = cloud_sql_instance.sync_sql_instances(
                neo4j_session,
                cloud_sql_cred,
                project_id,
                gcp_update_tag,
                common_job_parameters,
            )

            if instances_raw is not None:
                cloud_sql_database.sync_sql_databases(
                    neo4j_session,
                    cloud_sql_cred,
                    instances_raw,
                    project_id,
                    gcp_update_tag,
                    common_job_parameters,
                )

                cloud_sql_user.sync_sql_users(
                    neo4j_session,
                    cloud_sql_cred,
                    instances_raw,
                    project_id,
                    gcp_update_tag,
                    common_job_parameters,
                )

                cloud_sql_backup_config.sync_sql_backup_configs(
                    neo4j_session,
                    instances_raw,
                    project_id,
                    gcp_update_tag,
                    common_job_parameters,
                )

        if service_names.secretsmanager in enabled_services:
            logger.info("Syncing GCP project %s for Secret Manager.", project_id)
            secretsmanager_client = _get_cached_client(
                client_cache,
                "secretmanager",
                "v1",
                credentials,
            )
            secretsmanager.sync(
                neo4j_session,
                secretsmanager_client,
                project_id,
                gcp_update_tag,
                common_job_parameters,
            )

        if service_names.artifact_registry in enabled_services:
            logger.info("Syncing GCP project %s for Artifact Registry.", project_id)
            artifact_registry_client = _get_cached_client(
                client_cache,
                "artifactregistry",
                "v1",
                credentials,
            )
            artifact_registry.sync(
                neo4j_session,
                artifact_registry_client,
                credentials,
                project_id,
                gcp_update_tag,
                common_job_parameters,
            )

        if service_names.cloud_run in enabled_services:
            logger.info("Syncing GCP project %s for Cloud Run.", project_id)
            cloud_run_clients = cast(
                CloudRunClients,
                _get_cached(
                    client_cache,
                    ("run-gapic", "v2"),
                    lambda: build_cloud_run_clients(credentials=credentials),
                ),
            )
            cloud_run_locations = cloudrun_util.discover_cloud_run_locations(
                project_id,
                credentials=credentials,
            )
            if cloud_run_locations is None:
                logger.warning(
                    "Skipping Cloud Run sync for project %s because location discovery failed.",
                    project_id,
                )
            else:
                services_raw = cloudrun_service.sync_services(
                    neo4j_session,
                    cloud_run_clients.services,
                    project_id,
                    gcp_update_tag,
                    common_job_parameters,
                    locations=cloud_run_locations,
                )
                if services_raw is not None:
                    cloudrun_revision.sync_revisions(
                        neo4j_session,
                        cloud_run_clients.revisions,
                        project_id,
                        gcp_update_tag,
                        common_job_parameters,
                        services_raw=services_raw,
                        credentials=credentials,
                        services_client=cloud_run_clients.services,
                    )
                jobs_raw = cloudrun_job.sync_jobs(
                    neo4j_session,
                    cloud_run_clients.jobs,
                    project_id,
                    gcp_update_tag,
                    common_job_parameters,
                    credentials=credentials,
                    locations=cloud_run_locations,
                )
                if jobs_raw is not None:
                    cloudrun_execution.sync_executions(
                        neo4j_session,
                        cloud_run_clients.executions,
                        project_id,
                        gcp_update_tag,
                        common_job_parameters,
                        credentials=credentials,
                        jobs_raw=jobs_raw,
                        jobs_client=cloud_run_clients.jobs,
                    )

        bigquery_gapic_client = None
        bigquery_routine_client = None
        if service_names.bigquery in enabled_services:
            bigquery_gapic_client = _get_cached(
                client_cache,
                ("bigquery-gapic", "v1"),
                lambda: build_bigquery_client(credentials=credentials),
            )
            bigquery_routine_client = _get_cached_client(
                client_cache,
                "bigquery",
                "v2",
                credentials,
            )

        datasets_raw = None
        if bigquery_gapic_client is not None:
            logger.info("Syncing GCP project %s for BigQuery.", project_id)
            datasets_raw = bigquery_dataset.sync_bigquery_datasets(
                neo4j_session,
                bigquery_gapic_client,
                project_id,
                gcp_update_tag,
                common_job_parameters,
                credentials=credentials,
            )

        if service_names.bigquery_connection in enabled_services:
            logger.info("Syncing GCP project %s for BigQuery connections.", project_id)
            bigquery_conn_client = _get_cached(
                client_cache,
                ("bigqueryconnection-gapic", "v1"),
                lambda: build_bigquery_connection_client(credentials=credentials),
            )
            bigquery_connection.sync_bigquery_connections(
                neo4j_session,
                bigquery_conn_client,
                project_id,
                gcp_update_tag,
                common_job_parameters,
                bigquery_client=bigquery_gapic_client,
                datasets_raw=datasets_raw,
            )

        if bigquery_gapic_client is not None and datasets_raw is not None:
            bigquery_table.sync_bigquery_tables(
                neo4j_session,
                bigquery_gapic_client,
                datasets_raw,
                project_id,
                gcp_update_tag,
                common_job_parameters,
                credentials=credentials,
            )

            if bigquery_routine_client is not None:
                bigquery_routine.sync_bigquery_routines(
                    neo4j_session,
                    bigquery_routine_client,
                    datasets_raw,
                    project_id,
                    gcp_update_tag,
                    common_job_parameters,
                )

        # Clean up project-level IAM resources (service accounts and project roles)
        # Only run cleanup if IAM sync succeeded to avoid deleting valid data
        # when sync was skipped due to permission issues.
        if iam_sync_succeeded:
            logger.debug(f"Running cleanup for IAM resources in project {project_id}")
            iam.cleanup_service_accounts(neo4j_session, common_job_parameters)
            iam.cleanup_project_roles(neo4j_session, common_job_parameters)
        else:
            logger.debug(
                f"Skipping IAM cleanup for project {project_id} - IAM sync did not complete"
            )

        # Scoped analysis jobs - run per project after all syncs.
        # `gcp_compute_exposure` computes node properties (exposed_internet flags).
        # `gcp_lb_exposure` materializes EXPOSE edges for traversal/explanations.
        # We keep them split because they serve different outputs and cleanup scopes.
        if requested_syncs is None or "compute" in requested_syncs:
            run_scoped_analysis_job(
                "gcp_compute_exposure.json",
                neo4j_session,
                common_job_parameters,
            )
            run_scoped_analysis_job(
                "gcp_lb_exposure.json",
                neo4j_session,
                common_job_parameters,
            )

        del common_job_parameters["PROJECT_ID"]


@timeit
def start_gcp_ingestion(
    neo4j_session: neo4j.Session,
    config: Config,
    credentials: Optional[GoogleCredentials] = None,
) -> None:
    """
    Starts the GCP ingestion process by initializing Google Application Default Credentials, creating the necessary
    resource objects, listing all GCP organizations and projects available to the GCP identity, and supplying that
    context to all intel modules.
    :param neo4j_session: The Neo4j session
    :param config: A `cartography.config` object
    :param credentials: Optional GCP credentials. If not provided, ADC will be used.
    :return: Nothing
    """
    # Initialize credentials from ADC if not provided. This ensures we have a single
    # credentials object used consistently across all API clients.
    if credentials is None:
        credentials = get_gcp_credentials()
        if credentials is None:
            raise RuntimeError(
                "GCP credentials are not available; cannot start GCP ingestion."
            )

    common_job_parameters = {
        "UPDATE_TAG": config.update_tag,
        "gcp_permission_relationships_file": config.gcp_permission_relationships_file,
    }
    client_cache: _ClientCache = {}

    requested_syncs: Set[str] | None = None
    if config.gcp_requested_syncs:
        requested_syncs = set(
            parse_and_validate_gcp_requested_syncs(config.gcp_requested_syncs),
        )
        logger.info(
            "GCP selective sync enabled for: %s", ", ".join(sorted(requested_syncs))
        )

        # Warn if modules are requested without their dependencies
        module_dependencies = {
            "policy_bindings": ["iam"],
            "permission_relationships": ["iam", "policy_bindings"],
            "bigquery_connection": ["bigquery"],
        }
        for module, dependencies in module_dependencies.items():
            if module in requested_syncs:
                missing_deps = [
                    dep for dep in dependencies if dep not in requested_syncs
                ]
                if missing_deps:
                    logger.warning(
                        "GCP module '%s' is requested without its dependencies %s. "
                        "Some relationships may not be created if the dependency data doesn't exist in Neo4j.",
                        module,
                        missing_deps,
                    )

    # IMPORTANT: We defer cleanup for hierarchical resources (orgs, folders, projects) and run them
    # in reverse order. This prevents orphaned nodes when a parent is deleted.
    # Without this, deleting an org would break its relationships to projects/folders, leaving them
    # disconnected and unable to be cleaned up by their own cleanup jobs.
    #
    # Order of operations:
    # 1. Sync all orgs
    # 2. For each org:
    #    a. Sync folders and projects
    #    b. Sync project resources (with immediate cleanup)
    #    c. Clean up projects and folders for this org
    # 3. Clean up all orgs at the end
    #
    # This ensures children are cleaned up before their parents.

    orgs = sync_gcp_organizations(
        neo4j_session,
        config.update_tag,
        common_job_parameters,
        credentials=credentials,
    )

    # Track org cleanup jobs to run at the very end
    org_cleanup_jobs = []

    # For each org, sync its folders and projects (as sub-resources), then ingest per-project services
    for org in orgs:
        org_resource_name = org.get("name", "")  # e.g., organizations/123456789012
        if not org_resource_name or "/" not in org_resource_name:
            logger.error(f"Invalid org resource name: {org_resource_name}")
            continue

        # Store the full resource name for cleanup operations
        common_job_parameters["ORG_RESOURCE_NAME"] = org_resource_name

        # Sync folders under org
        folders = sync_gcp_folders(
            neo4j_session,
            config.update_tag,
            common_job_parameters,
            org_resource_name,
            credentials=credentials,
        )

        # Sync projects under org and each folder
        projects = sync_gcp_projects(
            neo4j_session,
            org_resource_name,
            folders,
            config.update_tag,
            common_job_parameters,
            credentials=credentials,
        )

        # Sync organization-level IAM (predefined roles + custom org roles) ONCE per org.
        # This is done before project resources so that roles exist when policy bindings are created.
        # Gate behind iam or policy_bindings since these are the only modules that need role nodes.
        if (
            requested_syncs is None
            or "iam" in requested_syncs
            or "policy_bindings" in requested_syncs
        ):
            logger.info(
                f"Syncing organization-level IAM for {org_resource_name}",
            )
            iam_client = build_client("iam", "v1", credentials=credentials)
            iam.sync_org_iam(
                neo4j_session,
                iam_client,
                org_resource_name,
                config.update_tag,
                common_job_parameters,
            )

        # Ingest per-project resources (these run their own cleanup immediately since they're leaf nodes)
        _sync_project_resources(
            neo4j_session,
            projects,
            config.update_tag,
            common_job_parameters,
            credentials=credentials,
            client_cache=client_cache,
            requested_syncs=requested_syncs,
        )

        # Clean up org-level roles for this org (after all project resources have been synced)
        if (
            requested_syncs is None
            or "iam" in requested_syncs
            or "policy_bindings" in requested_syncs
        ):
            logger.debug(
                f"Running cleanup for org-level IAM roles in {org_resource_name}"
            )
            iam.cleanup_org_roles(neo4j_session, common_job_parameters)

        # Clean up projects and folders for this org (children before parents).
        # Use cascade_delete=True to also delete orphaned child resources when a
        # project/folder is deleted. This handles the case where a project was deleted
        # between syncs - its resources would otherwise remain as orphans since resource
        # cleanup is scoped to PROJECT_ID and we only sync existing projects.
        logger.debug(f"Running cleanup for projects and folders in {org_resource_name}")
        GraphJob.from_node_schema(
            GCPProjectSchema(), common_job_parameters, cascade_delete=True
        ).run(neo4j_session)
        GraphJob.from_node_schema(
            GCPFolderSchema(), common_job_parameters, cascade_delete=True
        ).run(neo4j_session)

        # Save org cleanup job for later (with cascade_delete for defense in depth)
        org_cleanup_jobs.append(
            (GCPOrganizationSchema, dict(common_job_parameters), True)
        )

        # Remove org ID from common job parameters after processing
        del common_job_parameters["ORG_RESOURCE_NAME"]

    # Run all org cleanup jobs at the very end, after all children have been cleaned up
    # Use cascade_delete=True to clean up any remaining org children
    logger.info("Running cleanup for GCP organizations")
    for schema_class, params, cascade in org_cleanup_jobs:
        GraphJob.from_node_schema(schema_class(), params, cascade_delete=cascade).run(
            neo4j_session
        )

    if requested_syncs is None or "compute" in requested_syncs:
        run_analysis_job(
            "gcp_ip_node_label_migration.json",
            neo4j_session,
            common_job_parameters,
        )

        run_analysis_job(
            "gcp_compute_instance_vpc_analysis.json",
            neo4j_session,
            common_job_parameters,
        )

    # DEPRECATED: compatibility migration for legacy role edges. Remove in v1.0.0.
    if requested_syncs is None or "iam" in requested_syncs:
        run_analysis_job(
            "gcp_role_resource_edge_migration.json",
            neo4j_session,
            common_job_parameters,
        )

    if requested_syncs is None or "gke" in requested_syncs:
        run_analysis_job(
            "gcp_gke_asset_exposure.json",
            neo4j_session,
            common_job_parameters,
        )

        run_analysis_job(
            "gcp_gke_basic_auth.json",
            neo4j_session,
            common_job_parameters,
        )

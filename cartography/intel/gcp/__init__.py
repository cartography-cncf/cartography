import json
import logging
import os
import time
from collections import namedtuple
from concurrent.futures import as_completed
from concurrent.futures import ThreadPoolExecutor
from typing import Any
from typing import Dict
from typing import List
from typing import Set

import googleapiclient.discovery
import neo4j
import requests
from google.oauth2 import credentials as creds
from googleapiclient.discovery import build
from googleapiclient.discovery import Resource
from neo4j import GraphDatabase
from oauth2client.client import ApplicationDefaultCredentialsError
from oauth2client.client import GoogleCredentials

from . import label
from .resources import RESOURCE_FUNCTIONS
from cartography.config import Config
from cartography.graph.session import Session
from cartography.intel.gcp import crm
from cartography.intel.gcp.auth import AuthHelper
from cartography.intel.gcp.util.common import parse_and_validate_gcp_requested_syncs
from cartography.util import run_analysis_job
from cartography.util import run_cleanup_job
from cartography.util import timeit

logger = logging.getLogger(__name__)
Resources = namedtuple(
    "Resources",
    "compute storage gke dns cloudfunction crm_v1 crm_v2 cloudkms cloudrun  \
        iam admin apigateway sql bigtable firestore apikey pubsub dataproc cloudmonitoring cloud_logging cloudcdn loadbalancer bigquery dataflow spanner pubsublite cloudtasks serviceusage policyanalyzer",
)

# Mapping of service short names to their full names as in docs. See https://developers.google.com/apis-explorer,
# and https://cloud.google.com/service-usage/docs/reference/rest/v1/services#ServiceConfig
Services = namedtuple(
    "Services",
    "compute storage gke dns cloudfunction crm_v1 crm_v2 cloudkms cloudrun iam admin apigateway sql bigtable firestore apikey pubsub dataproc cloudmonitoring cloud_logging cloudcdn loadbalancer bigquery dataflow spanner pubsublite cloudtasks serviceusage policyanalyzer",
)
service_names = Services(
    compute="compute.googleapis.com",
    storage="storage.googleapis.com",
    gke="container.googleapis.com",
    dns="dns.googleapis.com",
    cloudfunction="cloudfunctions.googleapis.com",
    crm_v1="cloudresourcemanager.googleapis.com",
    crm_v2="cloudresourcemanager.googleapis.com",
    cloudkms="cloudkms.googleapis.com",
    cloudrun="run.googleapis.com",
    iam="iam.googleapis.com",
    admin="admin.googleapis.com",
    apigateway="apigateway.googleapis.com",
    sql="sqladmin.googleapis.com",
    bigtable="bigtableadmin.googleapis.com",
    firestore="firestore.googleapis.com",
    apikey="apikeys.googleapis.com",
    pubsub="pubsub.googleapis.com",
    dataproc="dataproc.googleapis.com",
    cloudmonitoring="cloudmonitoring.googleapis.com",
    cloud_logging="cloud_logging.googleapis.com",
    cloudcdn="cloudcdn.googleapis.com",
    loadbalancer="loadbalancer.googleapis.com",
    bigquery="bigquery.googleapis.com",
    dataflow="dataflow.googleapis.com",
    spanner="spanner.googleapis.com",
    pubsublite="pubsublite.googleapis.com",
    cloudtasks="cloudtasks.googleapis.com",
    serviceusage="serviceusage.googleapis.com",
    policyanalyzer="policyanalyzer.googleapis.com",
)


def _get_iam_resource_v1(credentials: GoogleCredentials) -> Resource:
    """
    Instantiates a Google IAM v1 resource object to call the IAM API.
    See https://cloud.google.com/iam/docs/reference/rest.
    :param credentials: The GoogleCredentials object
    :return: A IAM v1 resource object
    """
    # cache_discovery=False to suppress extra warnings.
    return googleapiclient.discovery.build("iam", "v1", credentials=credentials, cache_discovery=False)


def _get_crm_resource_v1(credentials: GoogleCredentials) -> Resource:
    """
    Instantiates a Google Compute Resource Manager v1 resource object to call the Resource Manager API.
    See https://cloud.google.com/resource-manager/reference/rest/.
    :param credentials: The GoogleCredentials object
    :return: A CRM v1 resource object
    """
    # cache_discovery=False to suppress extra warnings.
    # See https://github.com/googleapis/google-api-python-client/issues/299#issuecomment-268915510 and related issues
    return googleapiclient.discovery.build("cloudresourcemanager", "v1", credentials=credentials, cache_discovery=False)


def _get_policyanalyzer_resource(credentials: GoogleCredentials) -> Resource:
    """
    Instantiates a policyanalyzer resource object.
    :param credentials: The GoogleCredentials object
    :return: A serviceusage resource object
    """
    return googleapiclient.discovery.build("policyanalyzer", "v1", credentials=credentials, cache_discovery=False)


def _get_policyanalyzer_resource(credentials: GoogleCredentials) -> Resource:
    """
    Instantiates a policyanalyzer resource object.
    :param credentials: The GoogleCredentials object
    :return: A serviceusage resource object
    """
    return googleapiclient.discovery.build("policyanalyzer", "v1", credentials=credentials, cache_discovery=False)


def _get_crm_resource_v2(credentials: GoogleCredentials) -> Resource:
    """
    Instantiates a Google Compute Resource Manager v2 resource object to call the Resource Manager API.
    We need a v2 resource object to query for GCP folders.
    :param credentials: The GoogleCredentials object
    :return: A CRM v2 resource object
    """
    return googleapiclient.discovery.build("cloudresourcemanager", "v2", credentials=credentials, cache_discovery=False)


def _get_cloudfunction_resource(credentials: GoogleCredentials) -> Resource:
    """
    Instantiates a cloud function resource object.
    See: https://cloud.google.com/functions/docs/reference/rest
    :param credentials: The GoogleCredentials object
    :return: A serviceusage resource object
    """
    return googleapiclient.discovery.build("cloudfunctions", "v1", credentials=credentials, cache_discovery=False)


def _get_pubsub_resource(credentials: GoogleCredentials) -> Resource:
    """
    Instantiates a cloud pubsub resource object.
    See: https://cloud.google.com/pubsub/docs/reference/rest
    :param credentials: The GoogleCredentials object
    :return: A serviceusage resource object
    """
    return googleapiclient.discovery.build("pubsub", "v1", credentials=credentials, cache_discovery=False)


def _get_cloud_logging_resource(credentials: GoogleCredentials) -> Resource:
    """
    Instantiates a cloud logging resource object.
    See: https://cloud.google.com/logging/docs/reference/v2/rest
    :param credentials: The GoogleCredentials object
    :return: A serviceusage resource object
    """
    return googleapiclient.discovery.build("logging", "v2", credentials=credentials, cache_discovery=False)


def _get_cloudmonitoring_resource(credentials: GoogleCredentials) -> Resource:
    """
    Instantiates a cloud monitoring resource object.
    See: https://cloud.google.com/monitoring/api/ref_v3/rest
    :param credentials: The GoogleCredentials object
    :return: A serviceusage resource object
    """
    return googleapiclient.discovery.build("monitoring", "v3", credentials=credentials, cache_discovery=False)


def _get_dataproc_resource(credentials: GoogleCredentials) -> Resource:
    """
    Instantiates a cloud dataproc resource object.
    See: https://cloud.google.com/dataproc/docs/reference/rest/
    :param credentials: The GoogleCredentials object
    :return: A serviceusage resource object
    """
    return googleapiclient.discovery.build("dataproc", "v1", credentials=credentials, cache_discovery=False)


def _get_compute_resource(credentials: GoogleCredentials) -> Resource:
    """
    Instantiates a Google Compute resource object to call the Compute API. This is used to pull zone, instance, and
    networking data. See https://cloud.google.com/compute/docs/reference/rest/v1/.
    :param credentials: The GoogleCredentials object
    :return: A Compute resource object
    """
    return googleapiclient.discovery.build("compute", "v1", credentials=credentials, cache_discovery=False)


def _get_storage_resource(credentials: GoogleCredentials) -> Resource:
    """
    Instantiates a Google Cloud Storage resource object to call the Storage API.
    This is used to pull bucket metadata and IAM Policies
    as well as list buckets in a specified project.
    See https://cloud.google.com/storage/docs/json_api/.
    :param credentials: The GoogleCredentials object
    :return: A Storage resource object
    """
    return googleapiclient.discovery.build("storage", "v1", credentials=credentials, cache_discovery=False)


def _get_container_resource(credentials: GoogleCredentials) -> Resource:
    """
    Instantiates a Google Cloud Container resource object to call the
    Container API. See: https://cloud.google.com/kubernetes-engine/docs/reference/rest/v1/.
    :param credentials: The GoogleCredentials object
    :return: A Container resource object
    """
    return googleapiclient.discovery.build("container", "v1", credentials=credentials, cache_discovery=False)


def _get_dns_resource(credentials: GoogleCredentials) -> Resource:
    """
    Instantiates a Google Cloud DNS resource object to call the
    Container API. See: https://cloud.google.com/dns/docs/reference/v1/.
    :param credentials: The GoogleCredentials object
    :return: A DNS resource object
    """
    return googleapiclient.discovery.build("dns", "v1", credentials=credentials, cache_discovery=False)


def _get_serviceusage_resource(credentials: GoogleCredentials) -> Resource:
    """
    Instantiates a serviceusage resource object.
    See: https://cloud.google.com/service-usage/docs/reference/rest/v1/operations/list.
    :param credentials: The GoogleCredentials object
    :return: A serviceusage resource object
    """
    return googleapiclient.discovery.build("serviceusage", "v1", credentials=credentials, cache_discovery=False)


def _get_cloudkms_resource(credentials: GoogleCredentials) -> Resource:
    """
    Instantiates a cloud kms resource object.
    See: https://cloud.google.com/kms/docs/reference/rest
    :param credentials: The GoogleCredentials object
    :return: A serviceusage resource object
    """
    return googleapiclient.discovery.build("cloudkms", "v1", credentials=credentials, cache_discovery=False)


def _get_cloudsql_resource(credentials: GoogleCredentials) -> Resource:
    """
    Instantiates a cloud sql resource object.
    See: https://cloud.google.com/sql/docs/mysql/admin-api/rest
    :param credentials: The GoogleCredentials object
    :return: A serviceusage resource object
    """
    return googleapiclient.discovery.build("sqladmin", "v1", credentials=credentials, cache_discovery=False)


def _get_cloudrun_resource(credentials: GoogleCredentials) -> Resource:
    """
    Instantiates a cloud run resource object.
    See: https://cloud.google.com/run/docs/reference/rest
    :param credentials: The GoogleCredentials object
    :return: A serviceusage resource object
    """
    return googleapiclient.discovery.build("run", "v1", credentials=credentials, cache_discovery=None)


def _get_iam_resource(credentials: GoogleCredentials) -> Resource:
    """
    Instantiates a IAM resource object
    See: https://cloud.google.com/iam/docs/reference/rest
    :param credentails: The GoogleCredentails object
    :return: A IAM resource object
    """
    return googleapiclient.discovery.build("iam", "v1", credentials=credentials, cache_discovery=False)


def _get_admin_resource(credentials: GoogleCredentials, config: Config) -> Resource:
    """
    Instantiates a Admin resource object
    See: https://developers.google.com/admin-sdk/directory/reference/rest
    :param credentails: The GoogleCredentails object
    :return: A admin resource object
    """
    if not config.credentials.get("account_email") or not config.credentials.get("google_workspace_user_email"):
        return googleapiclient.discovery.build("admin", "directory_v1", credentials=credentials, cache_discovery=False)

    now = int(time.time())
    payload = {
        "iss": config.credentials.get("account_email"),
        "sub": config.credentials.get("google_workspace_user_email", ""),
        "aud": "https://oauth2.googleapis.com/token",
        "iat": now,
        "exp": now + 3600,
        "scope": "https://www.googleapis.com/auth/admin.directory.user.readonly https://www.googleapis.com/auth/admin.directory.group.readonly https://www.googleapis.com/auth/admin.directory.group.member.readonly",
    }

    body = {
        "payload": json.dumps(payload),
    }

    try:
        iamcredentials = build("iamcredentials", "v1", credentials=credentials)
        signed_jwt = (
            iamcredentials.projects()
            .serviceAccounts()
            .signJwt(name=f"projects/-/serviceAccounts/{config.credentials.get('account_email')}", body=body)
            .execute()
        )
    except Exception as e:
        logger.debug(f"couldn't get signed jwt for {config.credentials.get('account_email')} - {e}")
        return googleapiclient.discovery.build("admin", "directory_v1", credentials=credentials, cache_discovery=False)

    token_url = "https://oauth2.googleapis.com/token"
    token_data = {
        "grant_type": "urn:ietf:params:oauth:grant-type:jwt-bearer",
        "assertion": signed_jwt.get("signedJwt"),
    }

    response = requests.post(token_url, data=token_data)

    if response.status_code == 200:
        delegated_access_token = response.json()["access_token"]
    else:
        logger.debug(
            f"couldn't get delegated access token for {config.credentials.get('account_email')} - {response.json()}",
        )
        return googleapiclient.discovery.build("admin", "directory_v1", credentials=credentials, cache_discovery=False)

    delegated_credentials = creds.Credentials(delegated_access_token)

    return googleapiclient.discovery.build(
        "admin",
        "directory_v1",
        credentials=delegated_credentials,
        cache_discovery=False,
    )


def _get_apigateway_resource(credentials: GoogleCredentials) -> Resource:
    """
    Instantiates a apigateway resource object.
    See: https://cloud.google.com/api-gateway/docs/reference/rest.
    :param credentials: The GoogleCredentials object
    :return: A serviceusage resource object
    """
    return googleapiclient.discovery.build("apigateway", "v1", credentials=credentials, cache_discovery=False)


def _get_cloudbigtable_resource(credentials: GoogleCredentials) -> Resource:
    """
    Instantiates a cloud bigtable resource object.
    See: https://cloud.google.com/bigtable/docs/reference/admin/rest
    :param credentials: The GoogleCredentials object
    :return: A serviceusage resource object
    """
    return googleapiclient.discovery.build("bigtableadmin", "v2", credentials=credentials, cache_discovery=False)


def _get_firestore_resource(credentials: GoogleCredentials) -> Resource:
    """
    Instantiates a cloud firestore resource object.
    See: https://cloud.google.com/firestore/docs/reference/rest
    :param credentials: The GoogleCredentials object
    :return: A serviceusage resource object
    """
    return googleapiclient.discovery.build("firestore", "v1", credentials=credentials, cache_discovery=False)


def _get_apikey_resource(credentials: GoogleCredentials) -> Resource:
    """
    Instantiates a cloud api key resource object.
    See: https://cloud.google.com/firestore/docs/reference/rest
    :param credentials: The GoogleCredentials object
    :return: A serviceusage resource object
    """
    return googleapiclient.discovery.build("apikeys", "v2", credentials=credentials, cache_discovery=False)


def _get_bigquery_resource(credentials: GoogleCredentials) -> Resource:
    """
    Instantiates a bigquery resource object.
    See: https://cloud.google.com/bigquery/docs/reference/rest
    :param credentials: The GoogleCredentials object
    :return: A serviceusage resource object
    """
    return googleapiclient.discovery.build("bigquery", "v2", credentials=credentials, cache_discovery=False)


def _get_dataflow_resource(credentials: GoogleCredentials) -> Resource:
    """
    Instantiates a dataflow resource object.
    See: https://cloud.google.com/dataflow/docs/reference/rest
    :param credentials: The GoogleCredentials object
    :return: A serviceusage resource object
    """
    return googleapiclient.discovery.build("dataflow", "v1b3", credentials=credentials, cache_discovery=False)


def _get_cloudtasks_resource(credentials: GoogleCredentials) -> Resource:
    """
    Instantiates a cloudtasks resource object.
    See: https://cloud.google.com/tasks/docs/reference/rest
    :param credentials: The GoogleCredentials object
    :return: A serviceusage resource object
    """
    return googleapiclient.discovery.build("cloudtasks", "v2", credentials=credentials, cache_discovery=False)


def _get_spanner_resource(credentials: GoogleCredentials) -> Resource:
    """
    Instantiates a spanner resource object.
    See: https://cloud.google.com/spanner/docs/reference/rest
    :param credentials: The GoogleCredentials object
    :return: A serviceusage resource object
    """
    return googleapiclient.discovery.build("spanner", "v1", credentials=credentials, cache_discovery=False)


def _get_pubsublite_resource(credentials: GoogleCredentials) -> Resource:
    """
    Instantiates a pubsublite resource object.
    See: https://cloud.google.com/pubsub/lite/docs/reference/rest
    :param credentials: The GoogleCredentials object
    :return: A serviceusage resource object
    """
    return googleapiclient.discovery.build("pubsublite", "v1", credentials=credentials, cache_discovery=False)


def _initialize_resources(credentials: GoogleCredentials, config: Config) -> Resource:
    """
    Create namedtuple of all resource objects necessary for GCP data gathering.
    :param credentials: The GoogleCredentials object
    :return: namedtuple of all resource objects
    """
    return Resources(
        crm_v1=_get_crm_resource_v1(credentials),
        crm_v2=_get_crm_resource_v2(credentials),
        compute=_get_compute_resource(credentials),
        storage=_get_storage_resource(credentials),
        gke=_get_container_resource(credentials),
        serviceusage=_get_serviceusage_resource(credentials),
        dns=_get_dns_resource(credentials),
        sql=_get_cloudsql_resource(credentials),
        bigtable=_get_cloudbigtable_resource(credentials),
        firestore=_get_firestore_resource(credentials),
        cloudkms=_get_cloudkms_resource(credentials),
        cloudrun=_get_cloudrun_resource(credentials),
        iam=_get_iam_resource(credentials),
        admin=_get_admin_resource(credentials, config),
        apigateway=_get_apigateway_resource(credentials),
        cloudfunction=_get_cloudfunction_resource(credentials),
        pubsub=_get_pubsub_resource(credentials),
        cloud_logging=_get_cloud_logging_resource(credentials),
        cloudmonitoring=_get_cloudmonitoring_resource(credentials),
        dataproc=_get_dataproc_resource(credentials),
        cloudcdn=_get_compute_resource(credentials),
        loadbalancer=_get_compute_resource(credentials),
        apikey=_get_apikey_resource(credentials),
        bigquery=_get_bigquery_resource(credentials),
        dataflow=_get_dataflow_resource(credentials),
        cloudtasks=_get_cloudtasks_resource(credentials),
        spanner=_get_spanner_resource(credentials),
        pubsublite=_get_pubsublite_resource(credentials),
        policyanalyzer=_get_policyanalyzer_resource(credentials),
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
        req = serviceusage.services().list(parent=f"projects/{project_id}", filter="state:ENABLED")
        services = set()
        while req is not None:
            res = req.execute()
            if "services" in res:
                services.update({svc["config"]["name"] for svc in res["services"]})
            req = serviceusage.services().list_next(previous_request=req, previous_response=res)
        return services
    except googleapiclient.discovery.HttpError as http_error:
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


def concurrent_execution(
    service: str,
    service_func: Any,
    config: Config,
    resource: Resource,
    common_job_parameters: Dict,
    gcp_update_tag: int,
    project_id: str,
    policyanalyzer: Resource,
    crm_v1: Resource,
    crm_v2: Resource,
    apikey: Resource,
    compute: Resource,
    regions: list,
    shared_neo4j_driver=None,
):
    tic = time.perf_counter()
    _status = "success"
    _err: Dict = {}
    _result = None

    if shared_neo4j_driver is not None:
        neo4j_driver = shared_neo4j_driver
    else:
        neo4j_auth = (config.neo4j_user, config.neo4j_password)
        neo4j_driver = GraphDatabase.driver(
            config.neo4j_uri,
            auth=neo4j_auth,
            max_connection_lifetime=config.neo4j_max_connection_lifetime,
        )
    try:
        if service == "iam":
            service_func(
                Session(neo4j_driver),
                resource,
                policyanalyzer,
                crm_v1,
                crm_v2,
                apikey,
                project_id,
                gcp_update_tag,
                common_job_parameters,
            )

        else:
            service_func(
                Session(neo4j_driver),
                resource,
                project_id,
                gcp_update_tag,
                common_job_parameters,
                regions,
            )
        _result = round(time.perf_counter() - tic, 4)
    except Exception as e:
        _status = "error"
        _err = {"error_type": type(e).__name__, "error_message": str(e)}
        logger.error(
            f"error to process service {service} project={project_id} - {e}",
            exc_info=True,
            stack_info=True,
        )
    finally:
        _elapsed = _result if _result is not None else round(time.perf_counter() - tic, 4)
        _ev: Dict = {
            "event": "gcp_service_timing",
            "project_id": project_id,
            "service": service,
            "run_mode": "parallel",
            "duration_seconds": _elapsed,
            "status": _status,
        }
        if _err:
            _ev.update(_err)
        logger.info(json.dumps(_ev))
    return _result if _result is not None else _elapsed


def _sync_single_project(
    neo4j_session: neo4j.Session,
    resources: Resource,
    requested_syncs: List[str],
    project_id: str,
    gcp_update_tag: int,
    common_job_parameters: Dict,
    config: Config,
) -> None:
    """
    Handles graph sync for a single GCP project.
    :param neo4j_session: The Neo4j session
    :param resources: namedtuple of the GCP resource objects
    :param project_id: The project ID number to sync.  See  the `projectId` field in
    https://cloud.google.com/resource-manager/reference/rest/v1/projects
    :param gcp_update_tag: The timestamp value to set our new Neo4j nodes with
    :param common_job_parameters: Other parameters sent to Neo4j
    :return: Nothing
    """

    _project_tic = time.perf_counter()
    _service_timings: Dict = {}
    _failed_services: Dict = {}
    logger.info(f"gcp project={project_id}: starting full sync")
    all_regions = get_all_regions(resources.compute, project_id)

    regions = []
    if len(config.params.get("regions", [])) > 0:
        input_regions = config.params.get("regions", [])

        # INFO: if it's an invalid region in input parameters, ignore those
        for region in input_regions:
            if region in all_regions:
                regions.append(region)

    else:
        regions = all_regions

    if os.environ.get("LOCAL_RUN", "0") == "1":
        # BEGIN - Sequential Run

        for func_name in requested_syncs:
            if func_name in RESOURCE_FUNCTIONS:
                logger.info(f"Processing {func_name}")
                _svc_tic = time.perf_counter()
                _svc_status = "success"
                _svc_err: Dict = {}
                try:
                    if func_name == "iam":
                        RESOURCE_FUNCTIONS[func_name](
                            neo4j_session,
                            resources.iam,
                            resources.policyanalyzer,
                            resources.crm_v1,
                            resources.crm_v2,
                            resources.apikey,
                            project_id,
                            gcp_update_tag,
                            common_job_parameters,
                        )

                    else:
                        RESOURCE_FUNCTIONS[func_name](
                            neo4j_session,
                            getattr(resources, func_name),
                            project_id,
                            gcp_update_tag,
                            common_job_parameters,
                            regions,
                        )
                except Exception as e:
                    _svc_status = "error"
                    _svc_err = {"error_type": type(e).__name__, "error_message": str(e)}
                    logger.warning(f"error to process service {func_name} - {e}")
                finally:
                    _svc_elapsed = round(time.perf_counter() - _svc_tic, 4)
                    _service_timings[func_name] = _svc_elapsed
                    if _svc_status == "error":
                        _failed_services[func_name] = _svc_err.get("error_type", "error")
                    _sev: Dict = {
                        "event": "gcp_service_timing",
                        "project_id": project_id,
                        "service": func_name,
                        "run_mode": "sequential",
                        "duration_seconds": _svc_elapsed,
                        "status": _svc_status,
                    }
                    if _svc_err:
                        _sev.update(_svc_err)
                    logger.info(json.dumps(_sev))
            else:
                logger.warning(
                    f'GCP sync function "{func_name}" was specified but does not exist. Did you misspell it?',
                )

        # END - Sequential Run

    else:
        # BEGIN - Parallel Run

        # Determine the resources available on the project.
        enabled_services = _services_enabled_on_project(resources.serviceusage, project_id)
        parallel_requests = [r for r in requested_syncs if r in RESOURCE_FUNCTIONS]
        neo4j_auth = (config.neo4j_user, config.neo4j_password)
        shared_driver = GraphDatabase.driver(
            config.neo4j_uri,
            auth=neo4j_auth,
            max_connection_lifetime=config.neo4j_max_connection_lifetime,
        )
        try:
            with ThreadPoolExecutor(max_workers=min(8, len(parallel_requests))) as executor:
                futures_map: Dict = {}
                for request in parallel_requests:
                    try:
                        _f = executor.submit(
                            concurrent_execution,
                            request,
                            RESOURCE_FUNCTIONS[request],
                            config,
                            getattr(resources, request),
                            common_job_parameters,
                            gcp_update_tag,
                            project_id,
                            resources.policyanalyzer,
                            resources.crm_v1,
                            resources.crm_v2,
                            resources.apikey,
                            resources.compute,
                            regions,
                            shared_driver,
                        )
                        futures_map[_f] = request
                    except Exception as e:
                        logger.warning(f"error to append service {request} in futures - {e}")

                for request in requested_syncs:
                    if request not in RESOURCE_FUNCTIONS:
                        logger.warning(
                            f'GCP sync function "{request}" was specified but does not exist. Did you misspell it?',
                        )

                for future in as_completed(futures_map):
                    _fn = futures_map.get(future)
                    _elapsed = future.result()
                    if _fn:
                        if _elapsed is not None:
                            _service_timings[_fn] = _elapsed
                        else:
                            _failed_services[_fn] = "error"
        finally:
            shared_driver.close()

        # END - Parallel Run

    for service_name in common_job_parameters["service_labels"]:
        common_job_parameters["service_label"] = service_name

        label.cleanup_labels(neo4j_session, common_job_parameters, service_name)

        del common_job_parameters["service_label"]

    logger.info(
        json.dumps({
            "event": "gcp_project_timing_summary",
            "project_id": project_id,
            "total_duration_seconds": round(time.perf_counter() - _project_tic, 4),
            "service_timings": _service_timings,
            "slowest_service": max(_service_timings, key=_service_timings.get) if _service_timings else None,
            "failed_services": _failed_services,
        }),
    )


def get_all_regions(compute: Resource, project_id: str):
    regions = []

    req = compute.regions().list(project=project_id)
    while req is not None:
        res = req.execute()
        for rg in res.get("items", []):
            regions.append(rg["name"])

        req = compute.regions().list_next(previous_request=req, previous_response=res)

    return regions


def _sync_multiple_projects(
    neo4j_session: neo4j.Session,
    resources: Resource,
    requested_syncs: List[str],
    projects: List[Dict],
    gcp_update_tag: int,
    common_job_parameters: Dict,
    config: Config,
) -> None:
    """
    Handles graph sync for multiple GCP projects.
    :param neo4j_session: The Neo4j session
    :param resources: namedtuple of the GCP resource objects
    :param: projects: A list of projects. At minimum, this list should contain a list of dicts with the key "projectId"
    defined; so it would look like this: [{"projectId": "my-project-id-12345"}].
    This is the returned data from `crm.get_gcp_projects()`.
    See https://cloud.google.com/resource-manager/reference/rest/v1/projects.
    :param gcp_update_tag: The timestamp value to set our new Neo4j nodes with
    :param common_job_parameters: Other parameters sent to Neo4j
    :return: Nothing
    """
    logger.info("Syncing %d GCP projects.", len(projects))
    crm.sync_gcp_projects(neo4j_session, projects, gcp_update_tag, common_job_parameters, resources.crm_v2)

    for project in projects:
        if common_job_parameters["GCP_PROJECT_ID"] != project["projectId"]:
            continue

        logger.info("Syncing GCP project %s.", common_job_parameters["GCP_PROJECT_ID"])
        _sync_single_project(
            neo4j_session,
            resources,
            requested_syncs,
            common_job_parameters["GCP_PROJECT_ID"],
            gcp_update_tag,
            common_job_parameters,
            config,
        )
        if config.refresh_entitlements:
            run_cleanup_job("gcp_unused_cleanup.json", neo4j_session, common_job_parameters)
        run_analysis_job(
            "gcp_storage_bucket_policy_analysis.json",
            neo4j_session,
            common_job_parameters,
        )
        run_analysis_job(
            "gcp_bigquery_dataset_analysis.json",
            neo4j_session,
            common_job_parameters,
        )
        run_analysis_job(
            "gcp_compute_firewall_analysis.json",
            neo4j_session,
            common_job_parameters,
        )
        run_analysis_job(
            "gcp_cloud_function_analysis.json",
            neo4j_session,
            common_job_parameters,
        )
        run_analysis_job(
            "gcp_compute_instance_analysis.json",
            neo4j_session,
            common_job_parameters,
        )
        run_analysis_job(
            "gcp_kms_keyring_analysis.json",
            neo4j_session,
            common_job_parameters,
        )
        run_analysis_job(
            "gcp_cloud_function_analysis.json",
            neo4j_session,
            common_job_parameters,
        )
        run_analysis_job(
            "gcp_sql_instance_analysis.json",
            neo4j_session,
            common_job_parameters,
        )
    del common_job_parameters["GCP_PROJECT_ID"]


@timeit
def start_gcp_ingestion(neo4j_session: neo4j.Session, config: Config) -> None:
    """
    Starts the GCP ingestion process by initializing Google Application Default Credentials, creating the necessary
    resource objects, listing all GCP organizations and projects available to the GCP identity, and supplying that
    context to all intel modules.
    :param neo4j_session: The Neo4j session
    :param config: A `cartography.config` object
    :return: Nothing
    """
    common_job_parameters: Dict = {
        "UPDATE_TAG": config.update_tag,
        "WORKSPACE_ID": config.params["workspace"]["id_string"],
        "GCP_PROJECT_ID": config.params["workspace"]["account_id"],
        "GOOGLE_WORKSPACE_USER_EMAIL": config.credentials.get("google_workspace_user_email", ""),
        "EXTERNAL_IDP": config.params.get("externalIdp", None),
        "GROUPS": config.params.get("groups", []),
        "service_labels": [],
        "pagination": {},
    }

    try:
        # Explicitly use Application Default Credentials.
        # See https://oauth2client.readthedocs.io/en/latest/source/
        #             oauth2client.client.html#oauth2client.client.OAuth2Credentials
        # credentials = GoogleCredentials.get_application_default()

        auth_helper = AuthHelper()
        credentials = auth_helper.get_credentials(config.credentials["token_uri"], config.credentials["account_email"])
        # credentials = GoogleCredentials.get_application_default()

    except ApplicationDefaultCredentialsError as e:
        logger.debug("Error occurred calling GoogleCredentials.get_application_default().", exc_info=True)
        logger.error(
            (
                "Unable to initialize Google Compute Platform creds. If you don't have GCP data or don't want to load "
                "GCP data then you can ignore this message. Otherwise, the error code is: %s "
                "Make sure your GCP credentials are configured correctly, your credentials file (if any) is valid, and "
                "that the identity you are authenticating to has the securityReviewer role attached."
            ),
            e,
        )
        return

    requested_syncs: List[str] = list(RESOURCE_FUNCTIONS.keys())
    if config.gcp_requested_syncs:
        gcp_requested_syncs_string = ""
        for service in config.gcp_requested_syncs:
            gcp_requested_syncs_string += f"{service.get('name', ' ')},"
            if service.get("pagination", None):
                pagination = service.get("pagination", {})
                pagination["hasNextPage"] = False
                common_job_parameters["pagination"][service.get("name", None)] = pagination
        requested_syncs = parse_and_validate_gcp_requested_syncs(gcp_requested_syncs_string[:-1])

    resources = _initialize_resources(credentials, config)

    # If we don't have perms to pull Orgs or Folders from GCP, we will skip safely
    crm.sync_gcp_organizations(neo4j_session, resources.crm_v1, config.update_tag, common_job_parameters)
    crm.sync_gcp_folders(neo4j_session, resources.crm_v2, config.update_tag, common_job_parameters)

    projects = crm.get_gcp_projects(resources.crm_v1)

    _sync_multiple_projects(
        neo4j_session,
        resources,
        requested_syncs,
        projects,
        config.update_tag,
        common_job_parameters,
        config,
    )

    common_job_parameters["GCP_PROJECT_ID"] = config.params["workspace"]["account_id"]

    run_analysis_job(
        "gcp_bigquery_dataset_analysis.json",
        neo4j_session,
        common_job_parameters,
    )

    run_analysis_job(
        "gcp_cloud_function_analysis.json",
        neo4j_session,
        common_job_parameters,
    )

    run_analysis_job(
        "gcp_compute_asset_inet_exposure.json",
        neo4j_session,
        common_job_parameters,
    )

    run_analysis_job(
        "gcp_compute_firewall_analysis.json",
        neo4j_session,
        common_job_parameters,
    )

    run_analysis_job(
        "gcp_compute_instance_analysis.json",
        neo4j_session,
        common_job_parameters,
    )

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

    run_analysis_job(
        "gcp_kms_keyring_analysis.json",
        neo4j_session,
        common_job_parameters,
    )

    run_analysis_job(
        "gcp_sql_instance_analysis.json",
        neo4j_session,
        common_job_parameters,
    )

    run_analysis_job(
        "gcp_storage_bucket_policy_analysis.json",
        neo4j_session,
        common_job_parameters,
    )

    del common_job_parameters["service_labels"]
    return common_job_parameters

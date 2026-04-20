import logging
from dataclasses import dataclass
from typing import Optional

import googleapiclient.discovery
import httplib2
from google.auth import default
from google.auth.credentials import Credentials as GoogleCredentials
from google.auth.exceptions import DefaultCredentialsError
from google.auth.transport.requests import AuthorizedSession
from google.cloud import bigquery
from google.cloud import bigquery_connection_v1
from google.cloud import run_v2
from google.cloud.asset_v1 import AssetServiceClient
from google_auth_httplib2 import AuthorizedHttp
from googleapiclient.discovery import Resource

logger = logging.getLogger(__name__)

# Default HTTP timeout (seconds) for Google API clients built via discovery.build
_GCP_HTTP_TIMEOUT = 120


@dataclass(frozen=True)
class CloudRunClients:
    services: run_v2.ServicesClient
    jobs: run_v2.JobsClient
    revisions: run_v2.RevisionsClient
    executions: run_v2.ExecutionsClient


def _authorized_http_with_timeout(
    credentials: GoogleCredentials,
    timeout: int = _GCP_HTTP_TIMEOUT,
) -> AuthorizedHttp:
    """
    Build an AuthorizedHttp with a per-request timeout, avoiding global socket timeouts.
    """
    return AuthorizedHttp(credentials, http=httplib2.Http(timeout=timeout))


def _resolve_credentials(
    credentials: Optional[GoogleCredentials] = None,
    quota_project_id: Optional[str] = None,
) -> GoogleCredentials:
    resolved_credentials = credentials or get_gcp_credentials(
        quota_project_id=quota_project_id,
    )
    if resolved_credentials is None:
        raise RuntimeError("GCP credentials are not available; cannot build client.")
    return resolved_credentials


def build_client(
    service: str,
    version: str = "v1",
    credentials: Optional[GoogleCredentials] = None,
    quota_project_id: Optional[str] = None,
) -> Resource:
    resolved_credentials = _resolve_credentials(
        credentials=credentials,
        quota_project_id=quota_project_id,
    )
    client = googleapiclient.discovery.build(
        service,
        version,
        http=_authorized_http_with_timeout(resolved_credentials),
        cache_discovery=False,
    )
    return client


def build_asset_client(
    credentials: Optional[GoogleCredentials] = None,
    quota_project_id: Optional[str] = None,
) -> AssetServiceClient:
    """
    Build an AssetServiceClient for the Cloud Asset API.

    :param credentials: Optional credentials to use. If not provided, ADC will be used.
    :param quota_project_id: Optional quota project ID for billing. If not provided,
        the ADC default project will be used.
    """
    resolved_credentials = _resolve_credentials(
        credentials=credentials,
        quota_project_id=quota_project_id,
    )
    return AssetServiceClient(credentials=resolved_credentials)


def build_authorized_session(
    credentials: Optional[GoogleCredentials] = None,
    quota_project_id: Optional[str] = None,
) -> AuthorizedSession:
    resolved_credentials = _resolve_credentials(
        credentials=credentials,
        quota_project_id=quota_project_id,
    )
    return AuthorizedSession(resolved_credentials)


def build_bigquery_client(
    credentials: Optional[GoogleCredentials] = None,
    quota_project_id: Optional[str] = None,
    project: Optional[str] = None,
) -> bigquery.Client:
    resolved_credentials = _resolve_credentials(
        credentials=credentials,
        quota_project_id=quota_project_id,
    )
    return bigquery.Client(project=project, credentials=resolved_credentials)


def build_bigquery_connection_client(
    credentials: Optional[GoogleCredentials] = None,
    quota_project_id: Optional[str] = None,
) -> bigquery_connection_v1.ConnectionServiceClient:
    resolved_credentials = _resolve_credentials(
        credentials=credentials,
        quota_project_id=quota_project_id,
    )
    return bigquery_connection_v1.ConnectionServiceClient(
        credentials=resolved_credentials,
    )


def build_cloud_run_clients(
    credentials: Optional[GoogleCredentials] = None,
    quota_project_id: Optional[str] = None,
) -> CloudRunClients:
    resolved_credentials = _resolve_credentials(
        credentials=credentials,
        quota_project_id=quota_project_id,
    )
    return CloudRunClients(
        services=run_v2.ServicesClient(credentials=resolved_credentials),
        jobs=run_v2.JobsClient(credentials=resolved_credentials),
        revisions=run_v2.RevisionsClient(credentials=resolved_credentials),
        executions=run_v2.ExecutionsClient(credentials=resolved_credentials),
    )


def get_gcp_credentials(
    quota_project_id: Optional[str] = None,
) -> Optional[GoogleCredentials]:
    """
    Gets access tokens for GCP API access.

    Note: We intentionally do NOT set a quota project automatically from ADC.
    When credentials have a quota_project_id set, Google requires the
    serviceusage.serviceUsageConsumer role on that project for most API calls.
    By not setting it, we let Google use default billing behavior which doesn't
    require this additional permission.

    :param quota_project_id: Optional explicit quota project ID. Only set this
        if you specifically need quota/billing charged to a particular project
        AND the identity has serviceusage.serviceUsageConsumer on that project.
    """
    try:
        # Explicitly use Application Default Credentials with the cloud-platform scope.
        credentials, _ = default(
            scopes=["https://www.googleapis.com/auth/cloud-platform"],
            quota_project_id=quota_project_id,
        )
        # Only set quota project if explicitly requested.
        # Do NOT automatically use the ADC project ID - this would require
        # serviceusage.serviceUsageConsumer permission on that project.
        if quota_project_id and credentials.quota_project_id is None:
            credentials = credentials.with_quota_project(quota_project_id)
        return credentials
    except DefaultCredentialsError as e:
        logger.debug(
            "Error occurred calling google.auth.default().",
            exc_info=True,
        )
        logger.error(
            (
                "Unable to initialize Google Compute Platform creds. If you don't have GCP data or don't want to load "
                "GCP data then you can ignore this message. Otherwise, the error code is: %s "
                "Make sure your GCP credentials are configured correctly, your credentials file (if any) is valid, and "
                "that the identity you are authenticating to has the securityReviewer role attached."
            ),
            e,
        )
    return None

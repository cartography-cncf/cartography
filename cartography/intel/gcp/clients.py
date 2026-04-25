import logging

import googleapiclient.discovery
import httplib2
from google.api_core.client_options import ClientOptions
from google.auth import default
from google.auth.credentials import Credentials as GoogleCredentials
from google.auth.exceptions import DefaultCredentialsError
from google.cloud.aiplatform_v1.services.dataset_service import DatasetServiceClient
from google.cloud.aiplatform_v1.services.endpoint_service import EndpointServiceClient
from google.cloud.aiplatform_v1.services.feature_registry_service import (
    FeatureRegistryServiceClient,
)
from google.cloud.aiplatform_v1.services.model_service import ModelServiceClient
from google.cloud.aiplatform_v1.services.pipeline_service import PipelineServiceClient
from google.cloud.artifactregistry_v1 import ArtifactRegistryClient
from google.cloud.asset_v1 import AssetServiceClient
from google.cloud.run_v2 import ExecutionsClient
from google.cloud.run_v2 import JobsClient
from google.cloud.run_v2 import RevisionsClient
from google.cloud.run_v2 import ServicesClient
from google_auth_httplib2 import AuthorizedHttp
from googleapiclient.discovery import Resource

logger = logging.getLogger(__name__)

# Default HTTP timeout (seconds) for Google API clients built via discovery.build
_GCP_HTTP_TIMEOUT = 120


def _authorized_http_with_timeout(
    credentials: GoogleCredentials,
    timeout: int = _GCP_HTTP_TIMEOUT,
) -> AuthorizedHttp:
    """
    Build an AuthorizedHttp with a per-request timeout, avoiding global socket timeouts.
    """
    return AuthorizedHttp(credentials, http=httplib2.Http(timeout=timeout))


def _resolve_credentials(
    credentials: GoogleCredentials | None = None,
    quota_project_id: str | None = None,
) -> GoogleCredentials:
    resolved_credentials = credentials or get_gcp_credentials(
        quota_project_id=quota_project_id,
    )
    if resolved_credentials is None:
        raise RuntimeError("GCP credentials are not available; cannot build client.")
    return resolved_credentials


def _vertex_ai_client_options(location: str) -> ClientOptions:
    return ClientOptions(api_endpoint=f"{location}-aiplatform.googleapis.com")


def build_client(
    service: str,
    version: str = "v1",
    credentials: GoogleCredentials | None = None,
    quota_project_id: str | None = None,
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
    credentials: GoogleCredentials | None = None,
    quota_project_id: str | None = None,
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


def build_artifact_registry_client(
    credentials: GoogleCredentials | None = None,
    quota_project_id: str | None = None,
) -> ArtifactRegistryClient:
    return ArtifactRegistryClient(
        credentials=_resolve_credentials(
            credentials=credentials,
            quota_project_id=quota_project_id,
        ),
    )


def build_vertex_ai_model_client(
    location: str,
    credentials: GoogleCredentials | None = None,
    quota_project_id: str | None = None,
) -> ModelServiceClient:
    return ModelServiceClient(
        credentials=_resolve_credentials(
            credentials=credentials,
            quota_project_id=quota_project_id,
        ),
        client_options=_vertex_ai_client_options(location),
    )


def build_vertex_ai_endpoint_client(
    location: str,
    credentials: GoogleCredentials | None = None,
    quota_project_id: str | None = None,
) -> EndpointServiceClient:
    return EndpointServiceClient(
        credentials=_resolve_credentials(
            credentials=credentials,
            quota_project_id=quota_project_id,
        ),
        client_options=_vertex_ai_client_options(location),
    )


def build_vertex_ai_dataset_client(
    location: str,
    credentials: GoogleCredentials | None = None,
    quota_project_id: str | None = None,
) -> DatasetServiceClient:
    return DatasetServiceClient(
        credentials=_resolve_credentials(
            credentials=credentials,
            quota_project_id=quota_project_id,
        ),
        client_options=_vertex_ai_client_options(location),
    )


def build_vertex_ai_pipeline_client(
    location: str,
    credentials: GoogleCredentials | None = None,
    quota_project_id: str | None = None,
) -> PipelineServiceClient:
    return PipelineServiceClient(
        credentials=_resolve_credentials(
            credentials=credentials,
            quota_project_id=quota_project_id,
        ),
        client_options=_vertex_ai_client_options(location),
    )


def build_vertex_ai_feature_registry_client(
    location: str,
    credentials: GoogleCredentials | None = None,
    quota_project_id: str | None = None,
) -> FeatureRegistryServiceClient:
    return FeatureRegistryServiceClient(
        credentials=_resolve_credentials(
            credentials=credentials,
            quota_project_id=quota_project_id,
        ),
        client_options=_vertex_ai_client_options(location),
    )


def build_cloud_run_service_client(
    credentials: GoogleCredentials | None = None,
    quota_project_id: str | None = None,
) -> ServicesClient:
    return ServicesClient(
        credentials=_resolve_credentials(
            credentials=credentials,
            quota_project_id=quota_project_id,
        ),
    )


def build_cloud_run_revision_client(
    credentials: GoogleCredentials | None = None,
    quota_project_id: str | None = None,
) -> RevisionsClient:
    return RevisionsClient(
        credentials=_resolve_credentials(
            credentials=credentials,
            quota_project_id=quota_project_id,
        ),
    )


def build_cloud_run_job_client(
    credentials: GoogleCredentials | None = None,
    quota_project_id: str | None = None,
) -> JobsClient:
    return JobsClient(
        credentials=_resolve_credentials(
            credentials=credentials,
            quota_project_id=quota_project_id,
        ),
    )


def build_cloud_run_execution_client(
    credentials: GoogleCredentials | None = None,
    quota_project_id: str | None = None,
) -> ExecutionsClient:
    return ExecutionsClient(
        credentials=_resolve_credentials(
            credentials=credentials,
            quota_project_id=quota_project_id,
        ),
    )


def get_gcp_credentials(
    quota_project_id: str | None = None,
) -> GoogleCredentials | None:
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

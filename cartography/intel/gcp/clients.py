import logging
from collections import namedtuple
from typing import Optional

import googleapiclient.discovery
import httplib2
from google.auth import default
from google.auth.credentials import Credentials as GoogleCredentials
from google.auth.exceptions import DefaultCredentialsError
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


def build_crm_v1_client(credentials: GoogleCredentials) -> Resource:
    return googleapiclient.discovery.build(
        "cloudresourcemanager",
        "v1",
        http=_authorized_http_with_timeout(credentials),
        cache_discovery=False,
    )


def build_crm_v2_client(credentials: GoogleCredentials) -> Resource:
    return googleapiclient.discovery.build(
        "cloudresourcemanager",
        "v2",
        http=_authorized_http_with_timeout(credentials),
        cache_discovery=False,
    )


def build_compute_client(credentials: GoogleCredentials) -> Resource:
    return googleapiclient.discovery.build(
        "compute",
        "v1",
        http=_authorized_http_with_timeout(credentials),
        cache_discovery=False,
    )


def build_storage_client(credentials: GoogleCredentials) -> Resource:
    return googleapiclient.discovery.build(
        "storage",
        "v1",
        http=_authorized_http_with_timeout(credentials),
        cache_discovery=False,
    )


def build_container_client(credentials: GoogleCredentials) -> Resource:
    return googleapiclient.discovery.build(
        "container",
        "v1",
        http=_authorized_http_with_timeout(credentials),
        cache_discovery=False,
    )


def build_dns_client(credentials: GoogleCredentials) -> Resource:
    return googleapiclient.discovery.build(
        "dns",
        "v1",
        http=_authorized_http_with_timeout(credentials),
        cache_discovery=False,
    )


def build_serviceusage_client(credentials: GoogleCredentials) -> Resource:
    return googleapiclient.discovery.build(
        "serviceusage",
        "v1",
        http=_authorized_http_with_timeout(credentials),
        cache_discovery=False,
    )


def build_iam_client(credentials: GoogleCredentials) -> Resource:
    return googleapiclient.discovery.build(
        "iam",
        "v1",
        http=_authorized_http_with_timeout(credentials),
        cache_discovery=False,
    )


GCPClients = namedtuple(
    "GCPClients",
    "compute container crm_v1 crm_v2 dns storage serviceusage iam",
)


def initialize_clients(credentials: GoogleCredentials) -> GCPClients:
    """
    Create namedtuple of all client objects necessary for GCP data gathering.
    Lazily build heavier per-project clients later.
    """
    return GCPClients(
        crm_v1=build_crm_v1_client(credentials),
        crm_v2=build_crm_v2_client(credentials),
        serviceusage=build_serviceusage_client(credentials),
        compute=None,
        container=None,
        dns=None,
        storage=None,
        iam=build_iam_client(credentials),
    )


def get_gcp_credentials() -> Optional[GoogleCredentials]:
    """
    Gets access tokens for GCP API access.
    """
    try:
        # Explicitly use Application Default Credentials with the cloud-platform scope.
        credentials, _ = default(
            scopes=["https://www.googleapis.com/auth/cloud-platform"],
        )
        return credentials
    except DefaultCredentialsError as e:
        logger.debug(
            "Error occurred calling GoogleCredentials.get_application_default().",
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

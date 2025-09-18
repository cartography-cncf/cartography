import logging
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


def build_client(service: str, version: str = "v1") -> Resource:
    credentials = get_gcp_credentials()
    if credentials is None:
        raise RuntimeError("GCP credentials are not available; cannot build client.")
    client = googleapiclient.discovery.build(
        service,
        version,
        http=_authorized_http_with_timeout(credentials),
        cache_discovery=False,
    )
    return client


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

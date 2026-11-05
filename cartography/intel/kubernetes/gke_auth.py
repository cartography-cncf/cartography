import base64
import ipaddress
import logging
import tempfile
from contextlib import contextmanager
from pathlib import Path
from threading import Lock
from typing import Any
from typing import Iterator

import google.auth
from google.auth import impersonated_credentials
from google.auth.credentials import Credentials
from google.auth.credentials import with_scopes_if_required
from google.auth.transport.requests import Request
from googleapiclient.errors import HttpError
from kubernetes.client import ApiClient
from kubernetes.client import Configuration
from requests.utils import DEFAULT_CA_BUNDLE_PATH

from cartography.intel.gcp.clients import build_client
from cartography.intel.gcp.gke_utils import parse_cluster_ref
from cartography.intel.gcp.util import classify_gcp_http_error
from cartography.intel.gcp.util import gcp_api_execute_with_retry
from cartography.intel.gcp.util import summarize_gcp_http_error
from cartography.intel.kubernetes.util import K8sClient
from cartography.util import timeit

logger = logging.getLogger(__name__)
SCOPES = (
    "https://www.googleapis.com/auth/cloud-platform",
    "https://www.googleapis.com/auth/userinfo.email",
)


def get_credentials(
    service_account: str | None = None,
    source: Credentials | None = None,
) -> Credentials:
    """
    Return `source` credentials, or Google ADC when none are given, optionally
    impersonating `service_account`.
    """
    if source is None:
        credentials, _ = google.auth.default(scopes=SCOPES)
    else:
        credentials = with_scopes_if_required(source, SCOPES)
    if service_account:
        credentials = impersonated_credentials.Credentials(
            source_credentials=credentials,
            target_principal=service_account,
            target_scopes=SCOPES,
        )
    return credentials


@timeit
def get_cluster(resource_name: str, credentials: Credentials) -> dict[str, Any] | None:
    """
    Read one cluster from the GKE control plane API (container.googleapis.com).

    This is the Google Cloud API, not the cluster's Kubernetes API server: it needs IAM
    `container.clusters.get`. Returns None when the cluster is missing or not readable.
    """
    reference = parse_cluster_ref(resource_name)
    try:
        container = build_client("container", "v1", credentials=credentials)
        cluster = gcp_api_execute_with_retry(
            container.projects()
            .locations()
            .clusters()
            .get(name=reference.resource_name)
        )
    except HttpError as e:
        if classify_gcp_http_error(e) in (
            "api_disabled",
            "billing_disabled",
            "forbidden",
            "not_found",
        ):
            logger.warning(
                "Could not read GKE cluster %s; skipping it. %s",
                reference.resource_name,
                summarize_gcp_http_error(e),
            )
            return None
        raise
    # Carry the requested project ID even when Google's selfLink uses a project number.
    cluster["resource_name"] = reference.resource_name
    return cluster


def select_endpoint(cluster: dict[str, Any], endpoint: str) -> tuple[str, bool]:
    """
    Return the Kubernetes API server URL for `endpoint` and whether its certificate is
    issued by a public CA (DNS endpoint) rather than the cluster CA (IP endpoints).
    """
    endpoints = cluster.get("controlPlaneEndpointsConfig") or {}
    if endpoint == "dns":
        dns = endpoints.get("dnsEndpointConfig") or {}
        hostname = dns.get("endpoint", "")
        if not dns.get("allowExternalTraffic") or not hostname.endswith(".gke.goog"):
            raise ValueError("GKE DNS access is not enabled for this cluster")
        if any(c in hostname for c in "/:@?#"):
            raise ValueError("Invalid GKE DNS endpoint")
        return f"https://{hostname}", True
    if endpoint not in ("private", "public"):
        raise ValueError("GKE endpoint must be dns, private, or public")
    ip_config = endpoints.get("ipEndpointsConfig")
    legacy = cluster.get("privateClusterConfig") or {}
    if ip_config is not None:
        if not ip_config.get("enabled"):
            raise ValueError("GKE IP endpoint access is disabled")
        if endpoint == "public" and not ip_config.get("enablePublicEndpoint"):
            raise ValueError("GKE public IP endpoint access is disabled")
        address = ip_config.get(f"{endpoint}Endpoint")
    else:
        if endpoint == "public" and legacy.get("enablePrivateEndpoint"):
            raise ValueError("GKE public IP endpoint access is disabled")
        address = legacy.get(f"{endpoint}Endpoint")
        if endpoint == "public" and not address:
            address = cluster.get("endpoint")
    if not address:
        raise ValueError(f"GKE {endpoint} endpoint is unavailable")
    parsed = ipaddress.ip_address(address)
    host = f"[{parsed}]" if parsed.version == 6 else str(parsed)
    return f"https://{host}", False


@contextmanager
def connect(
    cluster: dict[str, Any], credentials: Credentials, endpoint: str = "dns"
) -> Iterator[K8sClient]:
    """Create one isolated, refreshable Kubernetes client without a kubeconfig."""
    ref = parse_cluster_ref(cluster["resource_name"])
    host, public_ca = select_endpoint(cluster, endpoint)
    configuration = Configuration()
    configuration.host = host
    configuration.verify_ssl = True
    lock = Lock()

    def refresh(config: Configuration) -> None:
        with lock:
            if not credentials.valid:
                credentials.refresh(Request())
            config.api_key["authorization"] = f"Bearer {credentials.token}"

    configuration.refresh_api_key_hook = refresh
    refresh(configuration)
    with tempfile.TemporaryDirectory(prefix="cartography-gke-") as directory:
        if public_ca:
            configuration.ssl_ca_cert = DEFAULT_CA_BUNDLE_PATH
        else:
            ca_file = Path(directory) / "ca.crt"
            ca_file.write_bytes(
                base64.b64decode(
                    cluster["masterAuth"]["clusterCaCertificate"], validate=True
                )
            )
            configuration.ssl_ca_cert = str(ca_file)
        with ApiClient(configuration) as api_client:
            yield K8sClient(
                name=f"gke_{ref.project}_{ref.location}_{ref.name}",
                config_file="",
                external_id=ref.resource_name,
                api_client=api_client,
                gke_cluster=cluster,
                tls_diagnostics={
                    "api_server_url": host,
                    "kubeconfig_insecure_skip_tls_verify": False,
                    "kubeconfig_tls_configuration_status": (
                        "public_ca" if public_ca else "valid_config"
                    ),
                },
            )

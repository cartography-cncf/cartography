import base64
import logging
import ssl
from datetime import datetime
from typing import Any
from typing import Callable

from dateutil.parser import isoparse
from kubernetes import config
from kubernetes.client import ApiClient
from kubernetes.client import Configuration
from kubernetes.client import CoreV1Api
from kubernetes.client import CustomObjectsApi
from kubernetes.client import NetworkingV1Api
from kubernetes.client import RbacAuthorizationV1Api
from kubernetes.client import VersionApi
from kubernetes.client.exceptions import ApiException
from kubernetes.config.kube_config import KubeConfigMerger

logger = logging.getLogger(__name__)

# EKS bearer-token lifetime is ~15 min; mint just before use.
_EKS_TOKEN_TTL_SECONDS = 60


class KubernetesContextNotFound(Exception):
    pass


class K8CoreApiClient(CoreV1Api):
    def __init__(
        self,
        name: str,
        config_file: str,
        api_client: ApiClient | None = None,
    ) -> None:
        self.name = name
        if not api_client:
            api_client = config.new_client_from_config(
                context=name, config_file=config_file
            )
        super().__init__(api_client=api_client)


class K8NetworkingApiClient(NetworkingV1Api):
    def __init__(
        self,
        name: str,
        config_file: str,
        api_client: ApiClient | None = None,
    ) -> None:
        self.name = name
        if not api_client:
            api_client = config.new_client_from_config(
                context=name, config_file=config_file
            )
        super().__init__(api_client=api_client)


class K8CustomObjectsApiClient(CustomObjectsApi):
    def __init__(
        self,
        name: str,
        config_file: str,
        api_client: ApiClient | None = None,
    ) -> None:
        self.name = name
        if not api_client:
            api_client = config.new_client_from_config(
                context=name, config_file=config_file
            )
        super().__init__(api_client=api_client)


class K8VersionApiClient(VersionApi):
    def __init__(
        self,
        name: str,
        config_file: str,
        api_client: ApiClient | None = None,
    ) -> None:
        self.name = name
        if not api_client:
            api_client = config.new_client_from_config(
                context=name, config_file=config_file
            )
        super().__init__(api_client=api_client)


class K8RbacApiClient(RbacAuthorizationV1Api):
    def __init__(
        self,
        name: str,
        config_file: str,
        api_client: ApiClient | None = None,
    ) -> None:
        self.name = name
        if not api_client:
            api_client = config.new_client_from_config(
                context=name, config_file=config_file
            )
        super().__init__(api_client=api_client)


class K8sClient:
    def __init__(
        self,
        name: str,
        config_file: str | None = None,
        external_id: str | None = None,
        api_client: ApiClient | None = None,
    ) -> None:
        self.name = name
        self.config_file = config_file
        self.external_id = external_id
        self.core = K8CoreApiClient(self.name, self.config_file, api_client)
        self.networking = K8NetworkingApiClient(self.name, self.config_file, api_client)
        self.version = K8VersionApiClient(self.name, self.config_file, api_client)
        self.rbac = K8RbacApiClient(self.name, self.config_file, api_client)
        self.custom = K8CustomObjectsApiClient(self.name, self.config_file, api_client)


def get_k8s_clients(kubeconfig: str) -> list[K8sClient]:
    # returns a tuple of (all contexts, current context)
    contexts, _ = config.list_kube_config_contexts(kubeconfig)
    if not contexts:
        raise KubernetesContextNotFound("No context found in kubeconfig.")

    clients = []
    for context in contexts:
        clients.append(
            K8sClient(
                context["name"],
                kubeconfig,
                external_id=context["context"].get("cluster"),
            ),
        )
    return clients


def _get_eks_token(cluster_name: str, boto3_session: Any) -> str:
    """Mint an EKS bearer token from a presigned STS GetCallerIdentity URL.

    Uses the boto3 session's STS client, so no aws CLI or kubeconfig exec plugin
    is required. The ``x-k8s-aws-id`` header EKS requires is attached to the
    GetCallerIdentity request via the client event system.
    """
    sts = boto3_session.client("sts")

    def _add_cluster_header(request, **kwargs):
        request.headers["x-k8s-aws-id"] = cluster_name

    sts.meta.events.register("before-sign.sts.GetCallerIdentity", _add_cluster_header)
    signed_url = sts.generate_presigned_url(
        "get_caller_identity",
        Params={},
        ExpiresIn=_EKS_TOKEN_TTL_SECONDS,
        HttpMethod="GET",
    )
    return "k8s-aws-v1." + base64.urlsafe_b64encode(
        signed_url.encode()
    ).decode().rstrip("=")


def _build_eks_api_client(endpoint: str, ca_cert_pem: str, token: str) -> ApiClient:
    """Build a kubernetes ApiClient for an EKS endpoint with a relaxed-but-verifying
    TLS context.

    EKS cluster CA certs do not carry an Authority Key Identifier extension, which
    Python 3.13 / urllib3 reject under the default VERIFY_X509_STRICT flag. We clear
    only that subflag; certificate verification against the cluster CA stays on
    (CERT_REQUIRED). This is not InsecureSkipVerify. The kubernetes client does not
    plumb a custom ssl_context through Configuration, so it is injected via the
    urllib3 pool args the RESTClientObject forwards.
    """
    ssl_context = ssl.create_default_context(cadata=ca_cert_pem)
    ssl_context.check_hostname = True
    ssl_context.verify_mode = ssl.CERT_REQUIRED
    ssl_context.verify_flags &= ~ssl.VERIFY_X509_STRICT

    cfg = Configuration()
    cfg.host = endpoint
    cfg.api_key = {"authorization": f"Bearer {token}"}
    cfg.verify_ssl = True

    api_client = ApiClient(configuration=cfg)
    api_client.rest_client.pool_manager.connection_pool_kw["ssl_context"] = ssl_context
    return api_client


def get_eks_k8s_clients(
    cluster_names: list[str], boto3_session: Any
) -> list[K8sClient]:
    """Build K8sClients for EKS clusters using boto3 auth instead of a kubeconfig file."""
    eks = boto3_session.client("eks")
    clients = []
    for cluster_name in cluster_names:
        described = eks.describe_cluster(name=cluster_name)["cluster"]
        ca_cert_pem = base64.b64decode(
            described["certificateAuthority"]["data"]
        ).decode()
        token = _get_eks_token(cluster_name, boto3_session)
        api_client = _build_eks_api_client(described["endpoint"], ca_cert_pem, token)
        clients.append(
            K8sClient(
                cluster_name,
                external_id=described["arn"],
                api_client=api_client,
            ),
        )
    return clients


def get_qualified_resource_name(namespace: str, name: str) -> str:
    return f"{namespace}/{name}"


def _get_kubeconfig_merger(kubeconfig: str) -> KubeConfigMerger:
    return KubeConfigMerger(kubeconfig)


def get_kubeconfig_tls_diagnostics(
    context_name: str, kubeconfig: str
) -> dict[str, Any]:
    diagnostics: dict[str, Any] = {
        "api_server_url": None,
        "kubeconfig_insecure_skip_tls_verify": None,
        "kubeconfig_has_certificate_authority_data": False,
        "kubeconfig_has_certificate_authority_file": False,
        "kubeconfig_ca_file_path": None,
        "kubeconfig_has_client_certificate": False,
        "kubeconfig_has_client_key": False,
        "kubeconfig_tls_configuration_status": "unknown",
    }

    try:
        merged_config = _get_kubeconfig_merger(kubeconfig).config
    except Exception as err:
        logger.warning(
            "Unable to parse kubeconfig '%s' for context '%s': %s",
            kubeconfig,
            context_name,
            err,
        )
        return diagnostics

    context = merged_config["contexts"].get_with_name(context_name, safe=True)
    if context is None:
        return diagnostics

    context_details = context.safe_get("context") or {}
    cluster_name = context_details.get("cluster")
    user_name = context_details.get("user")
    if not cluster_name:
        return diagnostics

    cluster = merged_config["clusters"].get_with_name(cluster_name, safe=True)
    if cluster is None:
        return diagnostics

    cluster_details = cluster.safe_get("cluster") or {}
    diagnostics["api_server_url"] = cluster_details.get("server")

    insecure_skip_tls_verify = cluster_details.get("insecure-skip-tls-verify")
    diagnostics["kubeconfig_insecure_skip_tls_verify"] = insecure_skip_tls_verify
    diagnostics["kubeconfig_has_certificate_authority_data"] = bool(
        cluster_details.get("certificate-authority-data"),
    )
    ca_file_path = cluster_details.get("certificate-authority")
    diagnostics["kubeconfig_has_certificate_authority_file"] = bool(ca_file_path)
    diagnostics["kubeconfig_ca_file_path"] = ca_file_path

    if user_name:
        user = merged_config["users"].get_with_name(user_name, safe=True)
        if user is not None:
            user_details = user.safe_get("user") or {}
            diagnostics["kubeconfig_has_client_certificate"] = bool(
                user_details.get("client-certificate")
                or user_details.get("client-certificate-data"),
            )
            diagnostics["kubeconfig_has_client_key"] = bool(
                user_details.get("client-key") or user_details.get("client-key-data"),
            )

    if insecure_skip_tls_verify is True:
        diagnostics["kubeconfig_tls_configuration_status"] = "insecure_skip_tls"
    elif (
        diagnostics["kubeconfig_has_certificate_authority_data"]
        or diagnostics["kubeconfig_has_certificate_authority_file"]
    ):
        diagnostics["kubeconfig_tls_configuration_status"] = "valid_config"
    else:
        diagnostics["kubeconfig_tls_configuration_status"] = "missing_ca_material"

    return diagnostics


def get_epoch(date: datetime | None) -> int | None:
    if date:
        return int(date.timestamp())
    return None


def parse_rfc3339(value: str | None) -> datetime | None:
    """
    Parse an RFC3339 timestamp string (e.g. ``2024-01-02T03:04:05Z``) into a
    datetime. The Kubernetes ``CustomObjectsApi`` returns metadata timestamps
    as raw strings rather than as datetimes (unlike the typed apis), so callers
    that need an epoch int should do ``get_epoch(parse_rfc3339(value))``.
    """
    if not value:
        return None
    return isoparse(value)


def k8s_paginate(
    list_func: Callable,
    raise_on_forbidden: bool = False,
    **kwargs: Any,
) -> list[dict[str, Any]]:
    """
    Handles pagination for a Kubernetes API call.

    :param list_func: The list function to call (e.g. client.core.list_pod_for_all_namespaces)
    :param raise_on_forbidden: When True, re-raise ApiException with status 401/403 so the caller
        can handle missing permissions (used for optional RBAC verbs). Other ApiExceptions are still
        logged and swallowed.
    :param kwargs: Keyword arguments to pass to the list function (e.g. limit=100)
    :return: A list of all resources returned by the list function
    """
    all_resources = []
    continue_token = None
    limit = kwargs.pop("limit", 100)
    function_name = list_func.__name__

    logger.debug(f"Starting pagination for {function_name} with limit {limit}.")

    while True:
        try:
            if continue_token:
                response = list_func(limit=limit, _continue=continue_token, **kwargs)
            else:
                response = list_func(limit=limit, **kwargs)

            # Check if items exists on the response
            if not hasattr(response, "items"):
                logger.warning(
                    f"Response from {function_name} does not contain 'items' attribute."
                )
                break

            items_count = len(response.items)
            all_resources.extend(response.items)

            logger.debug(f"Retrieved {items_count} {function_name} resources")

            # Check if metadata exists on the response
            if not hasattr(response, "metadata"):
                logger.warning(
                    f"Response from {function_name} does not contain 'metadata' attribute."
                )
                break

            continue_token = response.metadata._continue
            if not continue_token:
                logger.debug(f"No more {function_name} resources to retrieve.")
                break

        except ApiException as e:
            if raise_on_forbidden and e.status in (401, 403):
                raise
            logger.error(
                f"Kubernetes API error retrieving {function_name} resources. {e}: {e.status} - {e.reason}"
            )
            break

    logger.debug(
        f"Completed pagination for {function_name}: retrieved {len(all_resources)} resources"
    )
    return all_resources

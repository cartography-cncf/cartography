import logging
from datetime import datetime
from typing import Any
from typing import Callable

from kubernetes import config
from kubernetes.client import ApiClient
from kubernetes.client import CoreV1Api
from kubernetes.client import NetworkingV1Api
from kubernetes.client import RbacAuthorizationV1Api
from kubernetes.client import VersionApi
from kubernetes.client.exceptions import ApiException
from kubernetes.config.kube_config import KubeConfigMerger

logger = logging.getLogger(__name__)


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
        config_file: str,
        external_id: str | None = None,
    ) -> None:
        self.name = name
        self.config_file = config_file
        self.external_id = external_id
        self.core = K8CoreApiClient(self.name, self.config_file)
        self.networking = K8NetworkingApiClient(self.name, self.config_file)
        self.version = K8VersionApiClient(self.name, self.config_file)
        self.rbac = K8RbacApiClient(self.name, self.config_file)


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


def k8s_paginate(
    list_func: Callable,
    **kwargs: Any,
) -> list[dict[str, Any]]:
    """
    Handles pagination for a Kubernetes API call.

    :param list_func: The list function to call (e.g. client.core.list_pod_for_all_namespaces)
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
            logger.error(
                f"Kubernetes API error retrieving {function_name} resources. {e}: {e.status} - {e.reason}"
            )
            break

    logger.debug(
        f"Completed pagination for {function_name}: retrieved {len(all_resources)} resources"
    )
    return all_resources

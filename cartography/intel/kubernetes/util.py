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

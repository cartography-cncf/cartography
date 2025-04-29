from datetime import datetime
from typing import List
from typing import Optional

from kubernetes import config
from kubernetes.client import ApiClient
from kubernetes.client import CoreV1Api
from kubernetes.client import NetworkingV1Api
from kubernetes.client import VersionApi


class KubernetesContextNotFound(Exception):
    pass


class K8CoreApiClient(CoreV1Api):
    def __init__(self, name: str, config_file: str, api_client: Optional[ApiClient] = None) -> None:
        self.name = name
        if not api_client:
            api_client = config.new_client_from_config(context=name, config_file=config_file)
        super().__init__(api_client=api_client)


class K8NetworkingApiClient(NetworkingV1Api):
    def __init__(self, name: str, config_file: str, api_client: Optional[ApiClient] = None) -> None:
        self.name = name
        if not api_client:
            api_client = config.new_client_from_config(context=name, config_file=config_file)
        super().__init__(api_client=api_client)


class K8VersionApiClient(VersionApi):
    def __init__(self, name: str, config_file: str, api_client: Optional[ApiClient] = None) -> None:
        self.name = name
        if not api_client:
            api_client = config.new_client_from_config(context=name, config_file=config_file)
        super().__init__(api_client=api_client)


class K8sClient:
    def __init__(self, name: str, config_file: str, external_id: Optional[str] = None) -> None:
        self.name = name
        self.config_file = config_file
        self.external_id = external_id
        self.core = K8CoreApiClient(self.name, self.config_file)
        self.networking = K8NetworkingApiClient(self.name, self.config_file)
        self.version = K8VersionApiClient(self.name, self.config_file)


def get_k8s_clients(kubeconfig: str) -> List[K8sClient]:
    contexts, _ = config.list_kube_config_contexts(kubeconfig)  # returns a tuple of (all contexts, current context)
    if not contexts:
        raise KubernetesContextNotFound("No context found in kubeconfig.")
    clients = list()
    for context in contexts:
        clients.append(
            K8sClient(
                context["name"],
                kubeconfig,
                external_id=context["context"].get("cluster"),
            ),
        )
    return clients


def get_epoch(date: Optional[datetime]) -> Optional[int]:
    if date:
        return int(date.timestamp())
    return None

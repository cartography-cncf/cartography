from datetime import datetime
from typing import List
from typing import Union

from kubernetes import config
from kubernetes.client import ApiClient
from kubernetes.client import CoreV1Api
from kubernetes.client import NetworkingV1Api


class KubernetesContextNotFound(Exception):
    pass


class K8CoreApiClient(CoreV1Api):
    def __init__(self, name: str, config_file: str, api_client: ApiClient = None) -> None:
        self.name = name
        if not api_client:
            api_client = config.new_client_from_config(context=name, config_file=config_file)
        super().__init__(api_client=api_client)


class K8NetworkingApiClient(NetworkingV1Api):
    def __init__(self, name: str, config_file: str, api_client: ApiClient = None) -> None:
        self.name = name
        if not api_client:
            api_client = config.new_client_from_config(context=name, config_file=config_file)
        super().__init__(api_client=api_client)


class K8sClient:
    def __init__(self, name: str, config_file: str) -> None:
        self.name = name
        self.config_file = config_file
        self.core = K8CoreApiClient(self.name, self.config_file)
        self.networking = K8NetworkingApiClient(self.name, self.config_file)


def get_k8s_clients(kubeconfig: str) -> List[K8sClient]:
    contexts, _ = config.list_kube_config_contexts(kubeconfig)
    if not contexts:
        raise KubernetesContextNotFound("No context found in kubeconfig.")
    clients = list()
    for context in contexts:
        clients.append(K8sClient(context["name"], kubeconfig))
    return clients


def get_epoch(date: datetime) -> Union[int, None]:
    if date:
        return int(date.strftime("%s"))
    return None

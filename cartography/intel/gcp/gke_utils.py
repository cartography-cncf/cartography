import re
from dataclasses import dataclass


@dataclass(frozen=True)
class GKEClusterRef:
    project: str
    location: str
    name: str

    @property
    def resource_name(self) -> str:
        return f"projects/{self.project}/locations/{self.location}/clusters/{self.name}"


def parse_cluster_ref(value: str) -> GKEClusterRef:
    """Normalize API resource names, selfLinks, and gcloud kubeconfig references."""
    value = re.sub(r"^https://container\.googleapis\.com/v1(?:beta1)?/", "", value)
    match = re.fullmatch(
        r"projects/([a-zA-Z0-9-]+)/(?:locations|zones)/([a-z0-9-]+)/clusters/([a-z0-9-]+)",
        value,
    ) or re.fullmatch(r"gke_([a-zA-Z0-9-]+)_([a-z0-9-]+)_([a-z0-9-]+)", value)
    if match is None:
        raise ValueError("GKE cluster must identify its project, location, and name")
    return GKEClusterRef(*match.groups())


def instance_id_from_provider_id(value: str | None) -> str | None:
    match = re.fullmatch(r"gce://([^/]+)/([^/]+)/([^/]+)", value or "")
    if match is None:
        return None
    project, zone, name = match.groups()
    return f"projects/{project}/zones/{zone}/instances/{name}"

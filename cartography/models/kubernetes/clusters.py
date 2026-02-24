from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.nodes import ExtraNodeLabels


@dataclass(frozen=True)
class KubernetesClusterNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id")
    name: PropertyRef = PropertyRef("name", extra_index=True)
    creation_timestamp: PropertyRef = PropertyRef("creation_timestamp")
    external_id: PropertyRef = PropertyRef("external_id", extra_index=True)
    version: PropertyRef = PropertyRef("git_version")
    version_major: PropertyRef = PropertyRef("version_major")
    version_minor: PropertyRef = PropertyRef("version_minor")
    go_version: PropertyRef = PropertyRef("go_version")
    compiler: PropertyRef = PropertyRef("compiler")
    platform: PropertyRef = PropertyRef("platform")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class KubernetesClusterSchema(CartographyNodeSchema):
    label: str = "KubernetesCluster"
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(["Cluster"])
    properties: KubernetesClusterNodeProperties = KubernetesClusterNodeProperties()

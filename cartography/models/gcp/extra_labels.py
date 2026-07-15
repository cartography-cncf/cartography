from dataclasses import dataclass

from cartography.models.core.nodes import ExtraNodeLabel


@dataclass(frozen=True)
class GCPBucketLabelLabel(ExtraNodeLabel):
    """A gcp node participating in the shared GCPBucketLabel graph interface."""

    label: str = "GCPBucketLabel"


@dataclass(frozen=True)
class InstanceLabel(ExtraNodeLabel):
    """A gcp node participating in the shared Instance graph interface."""

    label: str = "Instance"


@dataclass(frozen=True)
class LabelLabel(ExtraNodeLabel):
    """A gcp node participating in the shared Label graph interface."""

    label: str = "Label"


@dataclass(frozen=True)
class NetworkInterfaceLabel(ExtraNodeLabel):
    """A gcp node participating in the shared NetworkInterface graph interface."""

    label: str = "NetworkInterface"

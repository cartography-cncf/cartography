from dataclasses import dataclass

from cartography.models.core.nodes import ExtraNodeLabel


@dataclass(frozen=True)
class DependencyLabel(ExtraNodeLabel):
    """A node participating in the shared Dependency graph interface."""

    label: str = "Dependency"


@dataclass(frozen=True)
class FixLabel(ExtraNodeLabel):
    """A node participating in the shared Fix graph interface."""

    label: str = "Fix"


@dataclass(frozen=True)
class GCPPrincipalLabel(ExtraNodeLabel):
    """A node participating in the shared GCPPrincipal graph interface."""

    label: str = "GCPPrincipal"


@dataclass(frozen=True)
class IpPermissionEgressLabel(ExtraNodeLabel):
    """A node participating in the shared IpPermissionEgress graph interface."""

    label: str = "IpPermissionEgress"


@dataclass(frozen=True)
class IpPermissionInboundLabel(ExtraNodeLabel):
    """A node participating in the shared IpPermissionInbound graph interface."""

    label: str = "IpPermissionInbound"


@dataclass(frozen=True)
class IpRangeLabel(ExtraNodeLabel):
    """A node participating in the shared IpRange graph interface."""

    label: str = "IpRange"


@dataclass(frozen=True)
class IpRuleLabel(ExtraNodeLabel):
    """A node participating in the shared IpRule graph interface."""

    label: str = "IpRule"


@dataclass(frozen=True)
class RiskLabel(ExtraNodeLabel):
    """A node participating in the shared Risk graph interface."""

    label: str = "Risk"

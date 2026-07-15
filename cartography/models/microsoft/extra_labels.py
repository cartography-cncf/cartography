from dataclasses import dataclass

from cartography.models.core.nodes import ExtraNodeLabel


@dataclass(frozen=True)
class EntraIdentityLabel(ExtraNodeLabel):
    """A microsoft node participating in the shared EntraIdentity graph interface."""

    label: str = "EntraIdentity"


@dataclass(frozen=True)
class EntraTenantLabel(ExtraNodeLabel):
    """A microsoft node participating in the shared EntraTenant graph interface."""

    label: str = "EntraTenant"

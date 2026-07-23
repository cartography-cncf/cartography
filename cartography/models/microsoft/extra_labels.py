from cartography.models.core.nodes import ExtraNodeLabel

ENTRA_IDENTITY = ExtraNodeLabel(
    label="EntraIdentity",
    description="A microsoft node participating in the shared EntraIdentity graph interface.",
)


ENTRA_PRINCIPAL = ExtraNodeLabel(
    label="EntraPrincipal",
    description="A Microsoft identity participating in the shared EntraPrincipal graph interface.",
)


ENTRA_TENANT = ExtraNodeLabel(
    label="EntraTenant",
    description="A microsoft node participating in the shared EntraTenant graph interface.",
)

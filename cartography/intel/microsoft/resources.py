# Microsoft resource names for selective sync.
# These are the valid values for --microsoft-requested-syncs. Entra datasets can
# be selected one at a time, as can Defender datasets; Intune and O365 run as whole
# units. The Entra tenant always syncs, because every other Microsoft node hangs
# off it. Each Defender dataset needs its own permission and is skipped when the
# tenant can't provide it.
ENTRA_RESOURCES: list[str] = [
    "domains",
    "users",
    "groups",
    "administrative_units",
    "applications",
    "service_principals",
    "app_role_assignments",
    "directory_roles",
    "federation",
]

DEFENDER_RESOURCES: list[str] = ["defender_machines", "defender_alerts"]

RESOURCE_FUNCTIONS: list[str] = [
    *ENTRA_RESOURCES,
    "intune",
    "o365",
    *DEFENDER_RESOURCES,
]

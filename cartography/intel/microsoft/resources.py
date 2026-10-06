# Microsoft resource names for selective sync.
# These are the valid values for --microsoft-requested-syncs. Entra datasets can
# be selected one at a time; Intune and O365 run as whole units. The Entra tenant
# always syncs, because every other Microsoft node hangs off it.
ENTRA_RESOURCES: list[str] = [
    "users",
    "groups",
    "administrative_units",
    "applications",
    "service_principals",
    "app_role_assignments",
    "directory_roles",
    "federation",
]

RESOURCE_FUNCTIONS: list[str] = [*ENTRA_RESOURCES, "intune", "o365"]

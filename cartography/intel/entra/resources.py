from cartography.intel.entra.applications import sync_entra_applications
from cartography.intel.entra.groups import sync_entra_groups
from cartography.intel.entra.ou import sync_entra_ous
from cartography.intel.entra.users import sync_entra_users

# This is a list so that we sync these resources in order.
# Data shape: [("resource_name", sync_function), ...]
# Each sync function will be called with the following arguments:
#   - neo4j_session
#   - config.entra_tenant_id
#   - config.entra_client_id
#   - config.entra_client_secret
#   - config.update_tag
#   - common_job_parameters
RESOURCE_FUNCTIONS = [
    ("users", sync_entra_users),
    ("groups", sync_entra_groups),
    ("ous", sync_entra_ous),
    ("applications", sync_entra_applications),
]

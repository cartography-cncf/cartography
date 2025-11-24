from cartography.rules.data.rules.cloud_security_product_deactivated import (
    cloud_security_product_deactivated,
)
from cartography.rules.data.rules.compute_instance_exposed import (
    compute_instance_exposed,
)
from cartography.rules.data.rules.database_instance_exposed import (
    database_instance_exposed,
)
from cartography.rules.data.rules.delegation_boundary_modifiable import (
    delegation_boundary_modifiable,
)
from cartography.rules.data.rules.identity_administration_privileges import (
    identity_administration_privileges,
)
from cartography.rules.data.rules.inactive_user_active_accounts import (
    inactive_user_active_accounts,
)
from cartography.rules.data.rules.malicious_npm_dependencies_shai_hulud import (
    malicious_npm_dependencies_shai_hulud,
)
from cartography.rules.data.rules.mfa_missing import missing_mfa_rule
from cartography.rules.data.rules.object_storage_public import object_storage_public
from cartography.rules.data.rules.policy_administration_privileges import (
    policy_administration_privileges,
)
from cartography.rules.data.rules.unmanaged_accounts import unmanaged_accounts
from cartography.rules.data.rules.workload_identity_admin_capabilities import (
    workload_identity_admin_capabilities,
)

# Rule registry - all available rules
RULES = {
    compute_instance_exposed.id: compute_instance_exposed,
    database_instance_exposed.id: database_instance_exposed,
    delegation_boundary_modifiable.id: delegation_boundary_modifiable,
    identity_administration_privileges.id: identity_administration_privileges,
    inactive_user_active_accounts.id: inactive_user_active_accounts,
    missing_mfa_rule.id: missing_mfa_rule,
    object_storage_public.id: object_storage_public,
    policy_administration_privileges.id: policy_administration_privileges,
    unmanaged_accounts.id: unmanaged_accounts,
    workload_identity_admin_capabilities.id: workload_identity_admin_capabilities,
    cloud_security_product_deactivated.id: cloud_security_product_deactivated,
    malicious_npm_dependencies_shai_hulud.id: malicious_npm_dependencies_shai_hulud,
}

from cartography.rules.data.findings.compute_instance_exposed import (
    compute_instance_exposed,
)
from cartography.rules.data.findings.database_instance_exposed import (
    database_instance_exposed,
)
from cartography.rules.data.findings.delegation_boundary_modifiable import (
    delegation_boundary_modifiable,
)
from cartography.rules.data.findings.identity_administration_privileges import (
    identity_administration_privileges,
)
from cartography.rules.data.findings.mfa_missing import missing_mfa_finding
from cartography.rules.data.findings.object_storage_public import object_storage_public
from cartography.rules.data.findings.policy_administration_privileges import (
    policy_administration_privileges,
)
from cartography.rules.data.findings.unmanaged_account import unmanaged_account
from cartography.rules.data.findings.workload_identity_admin_capabilities import (
    workload_identity_admin_capabilities,
)

# Finding registry - all available findings
FINDINGS = {
    compute_instance_exposed.id: compute_instance_exposed,
    database_instance_exposed.id: database_instance_exposed,
    delegation_boundary_modifiable.id: delegation_boundary_modifiable,
    identity_administration_privileges.id: identity_administration_privileges,
    missing_mfa_finding.id: missing_mfa_finding,
    object_storage_public.id: object_storage_public,
    policy_administration_privileges.id: policy_administration_privileges,
    unmanaged_account.id: unmanaged_account,
    workload_identity_admin_capabilities.id: workload_identity_admin_capabilities,
}

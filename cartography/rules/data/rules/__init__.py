from cartography.rules.data.rules.cis_aws_iam import cis_1_12_unused_credentials
from cartography.rules.data.rules.cis_aws_iam import cis_1_13_multiple_access_keys
from cartography.rules.data.rules.cis_aws_iam import cis_1_14_access_key_not_rotated
from cartography.rules.data.rules.cis_aws_iam import cis_1_15_user_direct_policies
from cartography.rules.data.rules.cis_aws_iam import cis_1_18_expired_certificates
from cartography.rules.data.rules.cis_aws_logging import cis_3_1_cloudtrail_multi_region
from cartography.rules.data.rules.cis_aws_logging import (
    cis_3_4_cloudtrail_log_validation,
)
from cartography.rules.data.rules.cis_aws_logging import cis_3_5_cloudtrail_cloudwatch
from cartography.rules.data.rules.cis_aws_logging import cis_3_7_cloudtrail_encryption
from cartography.rules.data.rules.cis_aws_networking import cis_5_1_unrestricted_ssh
from cartography.rules.data.rules.cis_aws_networking import cis_5_2_unrestricted_rdp
from cartography.rules.data.rules.cis_aws_networking import cis_5_4_default_sg_traffic
from cartography.rules.data.rules.cis_aws_networking import unrestricted_all_ports
from cartography.rules.data.rules.cis_aws_storage import cis_2_1_1_s3_versioning
from cartography.rules.data.rules.cis_aws_storage import cis_2_1_2_s3_mfa_delete
from cartography.rules.data.rules.cis_aws_storage import (
    cis_2_1_4_s3_block_public_access,
)
from cartography.rules.data.rules.cis_aws_storage import cis_2_1_5_s3_access_logging
from cartography.rules.data.rules.cis_aws_storage import cis_2_1_6_s3_encryption
from cartography.rules.data.rules.cis_aws_storage import cis_2_2_1_rds_encryption
from cartography.rules.data.rules.cis_aws_storage import cis_2_3_1_ebs_encryption
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
    # CIS AWS IAM Rules (Section 1)
    cis_1_12_unused_credentials.id: cis_1_12_unused_credentials,
    cis_1_13_multiple_access_keys.id: cis_1_13_multiple_access_keys,
    cis_1_14_access_key_not_rotated.id: cis_1_14_access_key_not_rotated,
    cis_1_15_user_direct_policies.id: cis_1_15_user_direct_policies,
    cis_1_18_expired_certificates.id: cis_1_18_expired_certificates,
    # CIS AWS Storage Rules (Section 2)
    cis_2_1_1_s3_versioning.id: cis_2_1_1_s3_versioning,
    cis_2_1_2_s3_mfa_delete.id: cis_2_1_2_s3_mfa_delete,
    cis_2_1_4_s3_block_public_access.id: cis_2_1_4_s3_block_public_access,
    cis_2_1_5_s3_access_logging.id: cis_2_1_5_s3_access_logging,
    cis_2_1_6_s3_encryption.id: cis_2_1_6_s3_encryption,
    cis_2_2_1_rds_encryption.id: cis_2_2_1_rds_encryption,
    cis_2_3_1_ebs_encryption.id: cis_2_3_1_ebs_encryption,
    # CIS AWS Logging Rules (Section 3)
    cis_3_1_cloudtrail_multi_region.id: cis_3_1_cloudtrail_multi_region,
    cis_3_4_cloudtrail_log_validation.id: cis_3_4_cloudtrail_log_validation,
    cis_3_5_cloudtrail_cloudwatch.id: cis_3_5_cloudtrail_cloudwatch,
    cis_3_7_cloudtrail_encryption.id: cis_3_7_cloudtrail_encryption,
    # CIS AWS Networking Rules (Section 5)
    cis_5_1_unrestricted_ssh.id: cis_5_1_unrestricted_ssh,
    cis_5_2_unrestricted_rdp.id: cis_5_2_unrestricted_rdp,
    cis_5_4_default_sg_traffic.id: cis_5_4_default_sg_traffic,
    unrestricted_all_ports.id: unrestricted_all_ports,
    # Security Rules
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

"""CIS benchmark framework helpers."""

from cartography.rules.spec.model import Framework

CIS_FRAMEWORK_SHORT_NAME = "CIS"

CIS_AWS_FRAMEWORK_NAME = "CIS AWS Foundations Benchmark"
CIS_AWS_SCOPE = "aws"
CIS_AWS_REVISION = "6.0.0"

CIS_GCP_FRAMEWORK_NAME = "CIS GCP Foundations Benchmark"
CIS_GCP_SCOPE = "gcp"
CIS_GCP_REVISION = "4.0"

CIS_KUBERNETES_FRAMEWORK_NAME = "CIS Kubernetes Benchmark"
CIS_KUBERNETES_SCOPE = "kubernetes"
CIS_KUBERNETES_REVISION = "1.12"

CIS_GOOGLE_WORKSPACE_FRAMEWORK_NAME = "CIS Google Workspace Foundations Benchmark"
CIS_GOOGLE_WORKSPACE_SCOPE = "googleworkspace"
CIS_GOOGLE_WORKSPACE_REVISION = "1.3"

CIS_AWS_CONTROL_TITLES = {
    "2.3": "Ensure no root user account access key exists",
    "2.4": "Ensure MFA is enabled for the root user account",
    "2.11": "Ensure credentials unused for 45 days or more are disabled",
    "2.12": "Ensure there is only one active access key for any single IAM user",
    "2.13": "Ensure access keys are rotated every 90 days or less",
    "2.14": "Ensure IAM users receive permissions only through groups",
    "2.15": "Ensure IAM policies that allow full '*:*' administrative privileges are not attached",
    "2.18": "Ensure that all expired SSL/TLS certificates stored in AWS IAM are removed",
    "3.1.2": "Ensure MFA Delete is enabled on S3 buckets",
    "3.1.4": "Ensure that S3 is configured with 'Block Public Access' enabled",
    "3.2.1": "Ensure that encryption-at-rest is enabled for RDS instances",
    "4.1": "Ensure CloudTrail is enabled in all regions",
    "4.2": "Ensure CloudTrail log file validation is enabled",
    "4.4": "Ensure that server access logging is enabled on the CloudTrail S3 bucket",
    "4.5": "Ensure CloudTrail logs are encrypted at rest using KMS CMKs",
    "6.1.1": "Ensure EBS volume encryption is enabled in all regions",
    "6.1.2": "Ensure CIFS access is restricted to trusted networks to prevent unauthorized access",
    "6.3": "Ensure no security groups allow ingress from 0.0.0.0/0 to remote server administration ports",
    "6.4": "Ensure no security groups allow ingress from ::/0 to remote server administration ports",
    "6.5": "Ensure the default security group of every VPC restricts all traffic",
    "6.7": "Ensure that the EC2 Metadata Service only allows IMDSv2",
}

CIS_GCP_CONTROL_TITLES = {
    "3.1": "Ensure That the Default Network Does Not Exist in a Project",
    "3.3": "Ensure That DNSSEC Is Enabled for Cloud DNS",
    "3.4": "Ensure That RSASHA1 Is Not Used for the Key-Signing Key in Cloud DNS DNSSEC",
    "3.5": "Ensure That RSASHA1 Is Not Used for the Zone-Signing Key in Cloud DNS DNSSEC",
    "3.6": "Ensure That SSH Access Is Restricted From the Internet",
    "3.7": "Ensure That RDP Access Is Restricted From the Internet",
    "3.8": "Ensure that VPC Flow Logs is Enabled for Every Subnet in a VPC Network",
    "4.1": "Ensure That Instances Are Not Configured To Use the Default Service Account",
    "4.2": "Ensure That Instances Are Not Configured To Use the Default Service Account With Full Access to All Cloud APIs",
    "4.3": 'Ensure "Block Project-Wide SSH Keys" Is Enabled for VM Instances',
    "4.4": "Ensure Oslogin Is Enabled for a Project",
    "4.5": "Ensure 'Enable Connecting to Serial Ports' Is Not Enabled for VM Instance",
    "4.6": "Ensure That IP Forwarding Is Not Enabled on Instances",
    "4.8": "Ensure Compute Instances Are Launched With Shielded VM Enabled",
    "4.9": "Ensure That Compute Instances Do Not Have Public IP Addresses",
    "4.11": "Ensure That Compute Instances Have Confidential Computing Enabled",
    "5.2": "Ensure That Cloud Storage Buckets Have Uniform Bucket-Level Access Enabled",
    "6.1.2": "Ensure 'Skip_show_database' Database Flag for Cloud SQL MySQL Instance Is Set to 'On'",
    "6.1.3": "Ensure That the 'Local_infile' Database Flag for a Cloud SQL MySQL Instance Is Set to 'Off'",
    "6.2.1": "Ensure 'Log_error_verbosity' Database Flag for Cloud SQL PostgreSQL Instance Is Set to 'DEFAULT' or Stricter",
    "6.2.2": "Ensure That the 'Log_connections' Database Flag for Cloud SQL PostgreSQL Instance Is Set to 'On'",
    "6.2.3": "Ensure That the 'Log_disconnections' Database Flag for Cloud SQL PostgreSQL Instance Is Set to 'On'",
    "6.2.5": "Ensure that the 'Log_min_messages' Flag for a Cloud SQL PostgreSQL Instance is set at minimum to 'Warning'",
    "6.2.6": "Ensure 'Log_min_error_statement' Database Flag for Cloud SQL PostgreSQL Instance Is Set to 'Error' or Stricter",
    "6.2.7": "Ensure That the 'Log_min_duration_statement' Database Flag for Cloud SQL PostgreSQL Instance Is Set to '-1' (Disabled)",
    "6.2.8": "Ensure That 'cloudsql.enable_pgaudit' Database Flag for each Cloud SQL PostgreSQL Instance Is Set to 'on' For Centralized Logging",
    "6.3.1": "Ensure 'external scripts enabled' Database Flag for Cloud SQL SQL Server Instance Is Set to 'off'",
    "6.3.2": "Ensure 'cross db ownership chaining' Database Flag for Cloud SQL SQL Server Instance Is Set to 'off'",
    "6.3.3": "Ensure 'user Connections' Database Flag for Cloud SQL SQL Server Instance Is Set to a Non-limiting Value",
    "6.3.4": "Ensure 'user options' Database Flag for Cloud SQL SQL Server Instance Is Not Configured",
    "6.3.5": "Ensure 'remote access' Database Flag for Cloud SQL SQL Server Instance Is Set to 'off'",
    "6.3.6": "Ensure '3625 (trace flag)' Database Flag for all Cloud SQL SQL Server Instances Is Set to 'on'",
    "6.3.7": "Ensure 'contained database authentication' Database Flag for Cloud SQL SQL Server Instance Is Set to 'off'",
    "6.4": "Ensure That the Cloud SQL Database Instance Requires All Incoming Connections To Use SSL",
    "6.5": "Ensure That Cloud SQL Database Instances Do Not Implicitly Whitelist All Public IP Addresses",
    "6.6": "Ensure That Cloud SQL Database Instances Do Not Have Public IPs",
    "6.7": "Ensure That Cloud SQL Database Instances Are Configured With Automated Backups",
    "7.1": "Ensure That BigQuery Datasets Are Not Anonymously or Publicly Accessible",
    "7.2": "Ensure That All BigQuery Tables Are Encrypted With Customer-Managed Encryption Key (CMEK)",
    "7.3": "Ensure That a Default Customer-Managed Encryption Key (CMEK) Is Specified for All BigQuery Data Sets",
}

CIS_KUBERNETES_CONTROL_TITLES = {
    "5.1.1": "Ensure that the cluster-admin role is only used where required",
    "5.1.2": "Minimize access to secrets",
    "5.1.3": "Minimize wildcard use in Roles and ClusterRoles",
    "5.1.4": "Minimize access to create pods",
    "5.1.5": "Ensure that default service accounts are not actively used.",
    "5.1.6": "Ensure that Service Account Tokens are only mounted where necessary",
    "5.1.7": "Avoid use of system:masters group",
    "5.1.8": "Limit use of the Bind, Impersonate and Escalate permissions in the Kubernetes cluster",
    "5.1.9": "Minimize access to create persistent volumes",
    "5.1.10": "Minimize access to the proxy sub-resource of nodes",
    "5.1.11": "Minimize access to the approval sub-resource of certificatesigningrequests objects",
    "5.1.12": "Minimize access to webhook configuration objects",
    "5.1.13": "Minimize access to the service account token creation",
    "5.2.3": "Minimize the admission of containers wishing to share the host process ID namespace",
    "5.2.4": "Minimize the admission of containers wishing to share the host IPC namespace",
    "5.2.5": "Minimize the admission of containers wishing to share the host network namespace",
    "5.2.6": "Minimize the admission of containers with allowPrivilegeEscalation",
    "5.2.11": "Minimize the admission of HostPath volumes",
    "5.2.12": "Minimize the admission of containers which use HostPorts",
    "5.4.1": "Prefer secrets as files over secrets as environment variables",
    "5.6.2": "Ensure that the seccomp profile is set to docker/default in your pod definitions",
    "5.6.4": "The default namespace should not be used",
}

CIS_GOOGLE_WORKSPACE_CONTROL_TITLES = {
    "1.1.1": "Ensure more than one Super Admin account exists",
    "1.1.2": "Ensure no more than 4 Super Admin accounts exist",
    "1.1.3": "Ensure super admin accounts are used only for super admin activities",
    "4.1.1.1": "Ensure 2-Step Verification (Multi-Factor Authentication) is enforced for all users in administrative roles",
    "4.1.1.3": "Ensure 2-Step Verification (Multi-Factor Authentication) is enforced for all users",
}


def _control_title(requirement: str, titles: dict[str, str]) -> str | None:
    # Match Framework.requirement normalization so helper lookups tolerate caller casing/spacing.
    return titles.get(requirement.strip().lower())


def cis_aws(requirement: str, control_title: str | None = None) -> Framework:
    return Framework(
        name=CIS_AWS_FRAMEWORK_NAME,
        short_name=CIS_FRAMEWORK_SHORT_NAME,
        scope=CIS_AWS_SCOPE,
        revision=CIS_AWS_REVISION,
        requirement=requirement,
        control_title=control_title
        or _control_title(requirement, CIS_AWS_CONTROL_TITLES),
    )


def cis_gcp(requirement: str, control_title: str | None = None) -> Framework:
    return Framework(
        name=CIS_GCP_FRAMEWORK_NAME,
        short_name=CIS_FRAMEWORK_SHORT_NAME,
        requirement=requirement,
        scope=CIS_GCP_SCOPE,
        revision=CIS_GCP_REVISION,
        control_title=control_title
        or _control_title(requirement, CIS_GCP_CONTROL_TITLES),
    )


def cis_kubernetes(requirement: str, control_title: str | None = None) -> Framework:
    return Framework(
        name=CIS_KUBERNETES_FRAMEWORK_NAME,
        short_name=CIS_FRAMEWORK_SHORT_NAME,
        scope=CIS_KUBERNETES_SCOPE,
        revision=CIS_KUBERNETES_REVISION,
        requirement=requirement,
        control_title=control_title
        or _control_title(requirement, CIS_KUBERNETES_CONTROL_TITLES),
    )


def cis_google_workspace(
    requirement: str, control_title: str | None = None
) -> Framework:
    return Framework(
        name=CIS_GOOGLE_WORKSPACE_FRAMEWORK_NAME,
        short_name=CIS_FRAMEWORK_SHORT_NAME,
        scope=CIS_GOOGLE_WORKSPACE_SCOPE,
        revision=CIS_GOOGLE_WORKSPACE_REVISION,
        requirement=requirement,
        control_title=control_title
        or _control_title(requirement, CIS_GOOGLE_WORKSPACE_CONTROL_TITLES),
    )

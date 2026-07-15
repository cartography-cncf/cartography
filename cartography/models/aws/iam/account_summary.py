from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema


@dataclass(frozen=True)
class AWSAccountSummaryNodeProperties(CartographyNodeProperties):
    """
    Composite node schema that adds IAM account summary properties to existing AWSAccount nodes.
    These properties come from the IAM GetAccountSummary API call.
    """

    id: PropertyRef = PropertyRef("id", description="The AWS Account ID number")
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last time the node was updated",
    )

    # Account security settings
    account_mfa_enabled: PropertyRef = PropertyRef(
        "AccountMFAEnabled",
        description="1 if the root account has MFA enabled, 0 otherwise. From IAM GetAccountSummary.",
    )
    mfa_devices: PropertyRef = PropertyRef(
        "MFADevices",
        description="Number of MFA devices registered in the account. From IAM GetAccountSummary.",
    )
    mfa_devices_in_use: PropertyRef = PropertyRef(
        "MFADevicesInUse",
        description="Number of MFA devices currently in use. From IAM GetAccountSummary.",
    )
    account_access_keys_present: PropertyRef = PropertyRef(
        "AccountAccessKeysPresent",
        description="1 if root account access keys exist, 0 otherwise. From IAM GetAccountSummary.",
    )
    account_signing_certificates_present: PropertyRef = PropertyRef(
        "AccountSigningCertificatesPresent",
        description="1 if root account signing certificates exist, 0 otherwise. From IAM GetAccountSummary.",
    )

    # Entity counts
    users: PropertyRef = PropertyRef(
        "Users",
        description="Number of IAM users in the account. From IAM GetAccountSummary.",
    )
    groups: PropertyRef = PropertyRef(
        "Groups",
        description="Number of IAM groups in the account. From IAM GetAccountSummary.",
    )
    roles: PropertyRef = PropertyRef(
        "Roles",
        description="Number of IAM roles in the account. From IAM GetAccountSummary.",
    )
    policies: PropertyRef = PropertyRef(
        "Policies",
        description="Number of IAM policies in the account. From IAM GetAccountSummary.",
    )
    instance_profiles: PropertyRef = PropertyRef(
        "InstanceProfiles",
        description="Number of instance profiles in the account. From IAM GetAccountSummary.",
    )
    providers: PropertyRef = PropertyRef(
        "Providers",
        description="Number of identity providers in the account. From IAM GetAccountSummary.",
    )
    server_certificates: PropertyRef = PropertyRef(
        "ServerCertificates",
        description="Number of server certificates in the account. From IAM GetAccountSummary.",
    )

    # Policy version usage
    policy_versions_in_use: PropertyRef = PropertyRef(
        "PolicyVersionsInUse",
        description="Number of policy versions in use. From IAM GetAccountSummary.",
    )


@dataclass(frozen=True)
class AWSAccountSummarySchema(CartographyNodeSchema):
    "Represents an AWS account."

    # Implementation note:
    # Composite schema that adds IAM account summary properties to existing AWSAccount
    # nodes.
    # No sub_resource_relationship since AWSAccount nodes are managed by the AWS account
    # sync.
    # No cleanup needed since these properties are just merged onto existing nodes each
    # sync.

    label: str = "AWSAccount"
    properties: AWSAccountSummaryNodeProperties = AWSAccountSummaryNodeProperties()

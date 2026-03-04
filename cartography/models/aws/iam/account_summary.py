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

    id: PropertyRef = PropertyRef("id")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)

    # Account security settings
    account_mfa_enabled: PropertyRef = PropertyRef("AccountMFAEnabled")
    mfa_devices: PropertyRef = PropertyRef("MFADevices")
    mfa_devices_in_use: PropertyRef = PropertyRef("MFADevicesInUse")
    account_access_keys_present: PropertyRef = PropertyRef("AccountAccessKeysPresent")
    account_signing_certificates_present: PropertyRef = PropertyRef(
        "AccountSigningCertificatesPresent"
    )

    # Entity counts
    users: PropertyRef = PropertyRef("Users")
    groups: PropertyRef = PropertyRef("Groups")
    roles: PropertyRef = PropertyRef("Roles")
    policies: PropertyRef = PropertyRef("Policies")
    instance_profiles: PropertyRef = PropertyRef("InstanceProfiles")
    providers: PropertyRef = PropertyRef("Providers")
    server_certificates: PropertyRef = PropertyRef("ServerCertificates")

    # Policy version usage
    policy_versions_in_use: PropertyRef = PropertyRef("PolicyVersionsInUse")


@dataclass(frozen=True)
class AWSAccountSummarySchema(CartographyNodeSchema):
    """
    Composite schema that adds IAM account summary properties to existing AWSAccount nodes.
    No sub_resource_relationship since AWSAccount nodes are managed by the AWS account sync.
    No cleanup needed since these properties are just merged onto existing nodes each sync.
    """

    label: str = "AWSAccount"
    properties: AWSAccountSummaryNodeProperties = AWSAccountSummaryNodeProperties()

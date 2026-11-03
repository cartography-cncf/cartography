from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.relationships import CartographyRelProperties
from cartography.models.core.relationships import CartographyRelSchema
from cartography.models.core.relationships import LinkDirection
from cartography.models.core.relationships import make_target_node_matcher
from cartography.models.core.relationships import OtherRelationships
from cartography.models.core.relationships import TargetNodeMatcher


@dataclass(frozen=True)
class DefenderMachineRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class DefenderMachineToTenantRel(CartographyRelSchema):
    """Links a Microsoft tenant to a Defender for Endpoint machine."""

    target_node_label: str = "AzureTenant"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("TENANT_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: DefenderMachineRelProperties = DefenderMachineRelProperties()


@dataclass(frozen=True)
class DefenderMachineNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "id", description="Tenant ID and Defender machine ID, separated by a slash."
    )
    machine_id: PropertyRef = PropertyRef(
        "machine_id", description="Machine ID assigned by Defender for Endpoint."
    )
    tenant_id: PropertyRef = PropertyRef(
        "TENANT_ID", set_in_kwargs=True, description="Microsoft tenant ID."
    )
    computer_dns_name: PropertyRef = PropertyRef(
        "computerDnsName",
        extra_index=True,
        description="Fully qualified DNS name of the machine.",
    )
    aad_device_id: PropertyRef = PropertyRef(
        "aadDeviceId",
        extra_index=True,
        description="Microsoft Entra device ID, when available.",
    )
    aad_device_id_normalized: PropertyRef = PropertyRef(
        "aad_device_id_normalized",
        extra_index=True,
        description="Lowercase aadDeviceId used for inventory joins; empty and all-zero IDs are excluded.",
    )
    is_aad_joined: PropertyRef = PropertyRef(
        "isAadJoined",
        description="Whether the machine is joined to Microsoft Entra ID.",
    )
    first_seen: PropertyRef = PropertyRef(
        "firstSeen",
        description="Native datetime from firstSeen: when Defender first observed the machine.",
    )
    last_seen: PropertyRef = PropertyRef(
        "lastSeen",
        description="Native datetime from lastSeen: when Defender last received a full device report (typically every 24 hours); not the portal's last-seen timestamp.",
    )
    os_platform: PropertyRef = PropertyRef(
        "osPlatform", description="Operating system platform reported by Defender."
    )
    os_version: PropertyRef = PropertyRef(
        "version", description="Operating system version reported by Defender."
    )
    os_build: PropertyRef = PropertyRef(
        "osBuild", description="Operating system build number."
    )
    health_status: PropertyRef = PropertyRef(
        "healthStatus", description="Defender sensor health status."
    )
    onboarding_status: PropertyRef = PropertyRef(
        "onboardingStatus",
        description="Defender onboarding status; inventory presence alone does not imply protection.",
    )
    risk_score: PropertyRef = PropertyRef(
        "riskScore", description="Defender device risk score."
    )
    exposure_level: PropertyRef = PropertyRef(
        "exposureLevel", description="Defender exposure level."
    )
    last_ip_address: PropertyRef = PropertyRef(
        "lastIpAddress", description="Last internal IP address reported by the machine."
    )
    last_external_ip_address: PropertyRef = PropertyRef(
        "lastExternalIpAddress",
        description="Last external IP address reported by the machine.",
    )
    machine_tags: PropertyRef = PropertyRef(
        "machineTags", description="Tags assigned to the machine."
    )
    rbac_group_id: PropertyRef = PropertyRef(
        "rbacGroupId", description="Defender device group ID."
    )
    rbac_group_name: PropertyRef = PropertyRef(
        "rbacGroupName", description="Defender device group name."
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class DefenderMachineToIntuneDeviceRel(CartographyRelSchema):
    """Matches Defender and Intune inventory by Entra device ID within the same tenant.

    Both producers write the same lowercase key; empty and all-zero device IDs
    never link. Entra users are reachable through the Intune enrollment.
    """

    target_node_label: str = "IntuneManagedDevice"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {
            "azure_ad_device_id_normalized": PropertyRef("aad_device_id_normalized"),
            "tenant_id": PropertyRef("TENANT_ID", set_in_kwargs=True),
        },
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "ASSOCIATED_WITH"
    properties: DefenderMachineRelProperties = DefenderMachineRelProperties()


@dataclass(frozen=True)
class DefenderMachineSchema(CartographyNodeSchema):
    """A machine observed by Microsoft Defender for Endpoint within the tenant's retention period.

    Presence in the inventory doesn't prove the endpoint is protected; see
    onboarding_status. The API provides no hardware serial number, so machines
    don't create canonical Device nodes; canonical devices are reachable through
    the linked IntuneManagedDevice.
    """

    label: str = "DefenderMachine"
    properties: DefenderMachineNodeProperties = DefenderMachineNodeProperties()
    sub_resource_relationship: DefenderMachineToTenantRel = DefenderMachineToTenantRel()
    other_relationships: OtherRelationships = OtherRelationships(
        [DefenderMachineToIntuneDeviceRel()]
    )

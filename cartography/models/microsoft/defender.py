from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.nodes import ExtraNodeLabels
from cartography.models.core.relationships import CartographyRelProperties
from cartography.models.core.relationships import CartographyRelSchema
from cartography.models.core.relationships import LinkDirection
from cartography.models.core.relationships import make_target_node_matcher
from cartography.models.core.relationships import OtherRelationships
from cartography.models.core.relationships import TargetNodeMatcher
from cartography.models.ontology.labels import SECURITY_ISSUE


@dataclass(frozen=True)
class DefenderRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class DefenderResourceToTenantRel(CartographyRelSchema):
    """Links a Microsoft tenant to its Defender for Endpoint resource."""

    target_node_label: str = "AzureTenant"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("TENANT_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: DefenderRelProperties = DefenderRelProperties()


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
    is_aad_joined: PropertyRef = PropertyRef(
        "isAadJoined",
        description="Whether the machine is joined to Microsoft Entra ID.",
    )
    first_seen: PropertyRef = PropertyRef(
        "firstSeen", description="When Defender first observed the machine."
    )
    last_seen: PropertyRef = PropertyRef(
        "lastSeen",
        description="When Defender last received a full device report (typically every 24 hours); not the portal's last-seen timestamp.",
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
    """Matches Defender and Intune inventory by Entra device ID within the same tenant."""

    target_node_label: str = "IntuneManagedDevice"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {
            "azure_ad_device_id": PropertyRef("aadDeviceId", ignore_case=True),
            "tenant_id": PropertyRef("TENANT_ID", set_in_kwargs=True),
        },
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "ASSOCIATED_WITH"
    properties: DefenderRelProperties = DefenderRelProperties()


@dataclass(frozen=True)
class DefenderMachineSchema(CartographyNodeSchema):
    """A machine observed by Microsoft Defender for Endpoint within the tenant's retention period."""

    label: str = "DefenderMachine"
    properties: DefenderMachineNodeProperties = DefenderMachineNodeProperties()
    sub_resource_relationship: DefenderResourceToTenantRel = (
        DefenderResourceToTenantRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [DefenderMachineToIntuneDeviceRel()]
    )


@dataclass(frozen=True)
class DefenderAlertNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "id", description="Tenant ID and Graph alert ID, separated by a slash."
    )
    alert_id: PropertyRef = PropertyRef(
        "alert_id", description="Microsoft Graph security alert ID."
    )
    tenant_id: PropertyRef = PropertyRef(
        "TENANT_ID", set_in_kwargs=True, description="Microsoft tenant ID."
    )
    provider_alert_id: PropertyRef = PropertyRef(
        "providerAlertId", description="Alert ID assigned by Defender for Endpoint."
    )
    incident_id: PropertyRef = PropertyRef(
        "incidentId", description="Incident ID associated with the alert."
    )
    title: PropertyRef = PropertyRef("title", description="Alert title.")
    severity: PropertyRef = PropertyRef(
        "severity", description="Alert severity reported by Microsoft Graph."
    )
    status: PropertyRef = PropertyRef(
        "status", description="Alert status; only unresolved alerts are ingested."
    )
    classification: PropertyRef = PropertyRef(
        "classification", description="Analyst classification of the alert."
    )
    determination: PropertyRef = PropertyRef(
        "determination", description="Analyst determination of the alert."
    )
    service_source: PropertyRef = PropertyRef(
        "serviceSource",
        description="Microsoft Defender service that produced the alert.",
    )
    detection_source: PropertyRef = PropertyRef(
        "detectionSource", description="Detection source that produced the alert."
    )
    categories: PropertyRef = PropertyRef(
        "categories", description="MITRE ATT&CK categories of suspicious activity."
    )
    threat_family_name: PropertyRef = PropertyRef(
        "threatFamilyName", description="Threat family identified in the alert."
    )
    mitre_techniques: PropertyRef = PropertyRef(
        "mitreTechniques",
        description="MITRE ATT&CK techniques identified in the alert.",
    )
    created_date_time: PropertyRef = PropertyRef(
        "createdDateTime", description="When the alert was created."
    )
    last_update_date_time: PropertyRef = PropertyRef(
        "lastUpdateDateTime", description="When the alert was last updated."
    )
    alert_web_url: PropertyRef = PropertyRef(
        "alertWebUrl", description="Alert URL in the Microsoft Defender portal."
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class DefenderAlertToMachineRel(CartographyRelSchema):
    """Links an alert to each Defender machine identified in its device evidence."""

    target_node_label: str = "DefenderMachine"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("machine_ids", one_to_many=True)},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "AFFECTS"
    properties: DefenderRelProperties = DefenderRelProperties()


@dataclass(frozen=True)
class DefenderAlertSchema(CartographyNodeSchema):
    """An unresolved Defender for Endpoint alert returned by Microsoft Graph security alerts v2.

    Ontology Mapping: The SecurityIssue label enables cross-provider security
    issue queries with normalized severity and resolution status.
    """

    label: str = "DefenderAlert"
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels([SECURITY_ISSUE])
    properties: DefenderAlertNodeProperties = DefenderAlertNodeProperties()
    sub_resource_relationship: DefenderResourceToTenantRel = (
        DefenderResourceToTenantRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [DefenderAlertToMachineRel()]
    )

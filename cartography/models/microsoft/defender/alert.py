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
class DefenderAlertRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class DefenderAlertToTenantRel(CartographyRelSchema):
    """Links a Microsoft tenant to a Defender alert."""

    target_node_label: str = "AzureTenant"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("TENANT_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: DefenderAlertRelProperties = DefenderAlertRelProperties()


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
    category: PropertyRef = PropertyRef(
        "category", description="MITRE ATT&CK category of the suspicious activity."
    )
    threat_family_name: PropertyRef = PropertyRef(
        "threatFamilyName", description="Threat family identified in the alert."
    )
    mitre_techniques: PropertyRef = PropertyRef(
        "mitreTechniques",
        description="MITRE ATT&CK techniques identified in the alert.",
    )
    created_date_time: PropertyRef = PropertyRef(
        "createdDateTime",
        description="Native datetime from createdDateTime: when the alert was created.",
    )
    last_update_date_time: PropertyRef = PropertyRef(
        "lastUpdateDateTime",
        description="Native datetime from lastUpdateDateTime: when the alert was last updated.",
    )
    alert_web_url: PropertyRef = PropertyRef(
        "alertWebUrl", description="Alert URL in the Microsoft Defender portal."
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class DefenderAlertToMachineRel(CartographyRelSchema):
    """Links an alert to each Defender machine identified in its device evidence.

    Machines outside the inventory's retention period aren't created as placeholders.
    """

    target_node_label: str = "DefenderMachine"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("machine_ids", one_to_many=True)},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "AFFECTS"
    properties: DefenderAlertRelProperties = DefenderAlertRelProperties()


@dataclass(frozen=True)
class DefenderAlertSchema(CartographyNodeSchema):
    """An unresolved Defender for Endpoint alert returned by Microsoft Graph security alerts v2.

    Ontology Mapping: The SecurityIssue label enables cross-provider security
    issue queries with normalized title, severity, status, type, and first-seen
    values. Unknown severity and status values stay unmapped.
    """

    label: str = "DefenderAlert"
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels([SECURITY_ISSUE])
    properties: DefenderAlertNodeProperties = DefenderAlertNodeProperties()
    sub_resource_relationship: DefenderAlertToTenantRel = DefenderAlertToTenantRel()
    other_relationships: OtherRelationships = OtherRelationships(
        [DefenderAlertToMachineRel()]
    )

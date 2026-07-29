from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.nodes import ExtraNodeLabels
from cartography.models.core.relationships import CartographyRelProperties
from cartography.models.core.relationships import CartographyRelSchema
from cartography.models.core.relationships import LinkDirection
from cartography.models.core.relationships import make_target_node_matcher
from cartography.models.core.relationships import TargetNodeMatcher
from cartography.models.ontology.labels import CVE


@dataclass(frozen=True)
class UbuntuCVENodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "id",
        description="CVE identifier prefixed with `USV|`, for example `USV|CVE-2024-1234`.",
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    cve_id: PropertyRef = PropertyRef(
        "cve_id",
        extra_index=True,
        description="CVE identifier without the Ubuntu prefix, for example `CVE-2024-1234`.",
    )
    description: PropertyRef = PropertyRef(
        "description", description="CVE description."
    )
    ubuntu_description: PropertyRef = PropertyRef(
        "ubuntu_description",
        description="Ubuntu-specific description of the vulnerability.",
    )
    priority: PropertyRef = PropertyRef(
        "priority",
        extra_index=True,
        description=(
            "Ubuntu priority rating: critical, high, medium, low or negligible."
        ),
    )
    status: PropertyRef = PropertyRef(
        "status",
        description="Status of the CVE in Ubuntu's tracker, for example active.",
    )
    cvss3: PropertyRef = PropertyRef(
        "cvss3", description="CVSS v3 score as published by Ubuntu on the CVE."
    )
    published: PropertyRef = PropertyRef(
        "published", description="Date the CVE was published."
    )
    updated_at: PropertyRef = PropertyRef(
        "updated_at", description="Date the CVE was last updated."
    )
    codename: PropertyRef = PropertyRef(
        "codename", description="Ubuntu release codename."
    )
    mitigation: PropertyRef = PropertyRef(
        "mitigation", description="Mitigation information, when Ubuntu provides any."
    )
    attack_vector: PropertyRef = PropertyRef(
        "attack_vector", description="CVSS v3 attack vector."
    )
    attack_complexity: PropertyRef = PropertyRef(
        "attack_complexity", description="CVSS v3 attack complexity."
    )
    base_score: PropertyRef = PropertyRef(
        "base_score",
        description="CVSS v3 base score from the CVE's baseMetricV3 impact data.",
    )
    base_severity: PropertyRef = PropertyRef(
        "base_severity", description="CVSS v3 base severity."
    )
    confidentiality_impact: PropertyRef = PropertyRef(
        "confidentiality_impact", description="CVSS v3 confidentiality impact."
    )
    integrity_impact: PropertyRef = PropertyRef(
        "integrity_impact", description="CVSS v3 integrity impact."
    )
    availability_impact: PropertyRef = PropertyRef(
        "availability_impact", description="CVSS v3 availability impact."
    )


@dataclass(frozen=True)
class UbuntuCVEToUbuntuCVEFeedRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class UbuntuCVEToUbuntuCVEFeedRel(CartographyRelSchema):
    """Links the Ubuntu Security feed to a CVE it publishes."""

    target_node_label: str = "UbuntuCVEFeed"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("FEED_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: UbuntuCVEToUbuntuCVEFeedRelProperties = (
        UbuntuCVEToUbuntuCVEFeedRelProperties()
    )


@dataclass(frozen=True)
class UbuntuCVESchema(CartographyNodeSchema):
    """A CVE as tracked by the [Ubuntu Security API](https://ubuntu.com/security/cves)."""

    label: str = "UbuntuCVE"
    properties: UbuntuCVENodeProperties = UbuntuCVENodeProperties()
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels([CVE])
    sub_resource_relationship: UbuntuCVEToUbuntuCVEFeedRel = (
        UbuntuCVEToUbuntuCVEFeedRel()
    )

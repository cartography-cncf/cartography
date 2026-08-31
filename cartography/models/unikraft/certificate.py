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
from cartography.models.ontology.labels import CERTIFICATE


@dataclass(frozen=True)
class UnikraftCertificateNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "uuid",
        description=(
            "Unikraft certificate UUID. Assumed globally unique across "
            "metros; see UnikraftInstanceNodeProperties.id."
        ),
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    name: PropertyRef = PropertyRef(
        "name", extra_index=True, description="Certificate name."
    )
    created_at: PropertyRef = PropertyRef(
        "created_at", description="Creation timestamp."
    )
    common_name: PropertyRef = PropertyRef(
        "common_name", description="Certificate common name."
    )
    subject: PropertyRef = PropertyRef("subject", description="Certificate subject.")
    issuer: PropertyRef = PropertyRef("issuer", description="Certificate issuer.")
    serial_number: PropertyRef = PropertyRef(
        "serial_number", description="Certificate serial number."
    )
    not_before: PropertyRef = PropertyRef(
        "not_before", description="Validity start timestamp."
    )
    not_after: PropertyRef = PropertyRef(
        "not_after", description="Validity end timestamp."
    )
    state: PropertyRef = PropertyRef(
        "state", description="Certificate lifecycle state."
    )
    status: PropertyRef = PropertyRef(
        "status", description="Operation status of the certificate."
    )
    message: PropertyRef = PropertyRef(
        "message", description="Additional status information."
    )
    metro: PropertyRef = PropertyRef(
        "METRO",
        set_in_kwargs=True,
        description="Unikraft metro this certificate was observed in.",
    )
    account_id: PropertyRef = PropertyRef(
        "ACCOUNT_ID", set_in_kwargs=True, description="Unikraft account UUID."
    )


@dataclass(frozen=True)
class UnikraftCertificateToAccountRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:UnikraftAccount)-[:RESOURCE]->(:UnikraftCertificate)
class UnikraftCertificateToAccountRel(CartographyRelSchema):
    """Connects `UnikraftAccount` to `UnikraftCertificate` through `RESOURCE`."""

    target_node_label: str = "UnikraftAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("ACCOUNT_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: UnikraftCertificateToAccountRelProperties = (
        UnikraftCertificateToAccountRelProperties()
    )


@dataclass(frozen=True)
class UnikraftCertificateSchema(CartographyNodeSchema):
    """Represents a TLS certificate managed in Unikraft Cloud."""

    label: str = "UnikraftCertificate"
    properties: UnikraftCertificateNodeProperties = UnikraftCertificateNodeProperties()
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels([CERTIFICATE])
    sub_resource_relationship: UnikraftCertificateToAccountRel = (
        UnikraftCertificateToAccountRel()
    )

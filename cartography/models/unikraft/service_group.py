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
from cartography.models.ontology.labels import LOAD_BALANCER


@dataclass(frozen=True)
class UnikraftServiceGroupNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "uuid",
        description=(
            "Unikraft service group UUID. Assumed globally unique across "
            "metros; see UnikraftInstanceNodeProperties.id."
        ),
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    name: PropertyRef = PropertyRef(
        "name", extra_index=True, description="Service group name."
    )
    created_at: PropertyRef = PropertyRef(
        "created_at", description="Creation timestamp."
    )
    persistent: PropertyRef = PropertyRef(
        "persistent",
        description="Whether the service group persists across restarts.",
    )
    autoscale: PropertyRef = PropertyRef(
        "autoscale", description="Whether autoscaling is enabled."
    )
    soft_limit: PropertyRef = PropertyRef(
        "soft_limit", description="Autoscale soft limit."
    )
    hard_limit: PropertyRef = PropertyRef(
        "hard_limit", description="Autoscale hard limit."
    )
    status: PropertyRef = PropertyRef(
        "status", description="Operation status of the service group."
    )
    message: PropertyRef = PropertyRef(
        "message", description="Additional status information."
    )
    domains: PropertyRef = PropertyRef(
        "domains",
        description="Fully-qualified domain names routed to this service group.",
    )
    primary_domain: PropertyRef = PropertyRef(
        "primary_domain",
        extra_index=True,
        description="First domain routed to this service group, used as its DNS endpoint.",
    )
    metro: PropertyRef = PropertyRef(
        "METRO",
        set_in_kwargs=True,
        description="Unikraft metro this service group runs in.",
    )
    account_id: PropertyRef = PropertyRef(
        "ACCOUNT_ID", set_in_kwargs=True, description="Unikraft account UUID."
    )


@dataclass(frozen=True)
class UnikraftServiceGroupToAccountRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:UnikraftAccount)-[:RESOURCE]->(:UnikraftServiceGroup)
class UnikraftServiceGroupToAccountRel(CartographyRelSchema):
    """Connects `UnikraftAccount` to `UnikraftServiceGroup` through `RESOURCE`."""

    target_node_label: str = "UnikraftAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("ACCOUNT_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: UnikraftServiceGroupToAccountRelProperties = (
        UnikraftServiceGroupToAccountRelProperties()
    )


@dataclass(frozen=True)
class UnikraftServiceGroupToInstanceRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:UnikraftServiceGroup)-[:EXPOSES]->(:UnikraftInstance)
class UnikraftServiceGroupToInstanceRel(CartographyRelSchema):
    """Connects `UnikraftServiceGroup` to the `UnikraftInstance`s it exposes."""

    target_node_label: str = "UnikraftInstance"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("instance_ids", one_to_many=True)},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "EXPOSES"
    properties: UnikraftServiceGroupToInstanceRelProperties = (
        UnikraftServiceGroupToInstanceRelProperties()
    )


@dataclass(frozen=True)
class UnikraftServiceGroupToCertificateRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:UnikraftServiceGroup)-[:SECURED_BY]->(:UnikraftCertificate)
class UnikraftServiceGroupToCertificateRel(CartographyRelSchema):
    """Connects `UnikraftServiceGroup` to the `UnikraftCertificate`s securing its domains."""

    target_node_label: str = "UnikraftCertificate"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("certificate_ids", one_to_many=True)},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "SECURED_BY"
    properties: UnikraftServiceGroupToCertificateRelProperties = (
        UnikraftServiceGroupToCertificateRelProperties()
    )


@dataclass(frozen=True)
class UnikraftServiceGroupSchema(CartographyNodeSchema):
    """Represents a Unikraft Cloud service group (DNS, routing, and TLS for exposed instances)."""

    label: str = "UnikraftServiceGroup"
    properties: UnikraftServiceGroupNodeProperties = (
        UnikraftServiceGroupNodeProperties()
    )
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels([LOAD_BALANCER])
    sub_resource_relationship: UnikraftServiceGroupToAccountRel = (
        UnikraftServiceGroupToAccountRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            UnikraftServiceGroupToInstanceRel(),
            UnikraftServiceGroupToCertificateRel(),
        ],
    )

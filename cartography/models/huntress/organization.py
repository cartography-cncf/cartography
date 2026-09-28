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
from cartography.models.ontology.labels import TENANT


@dataclass(frozen=True)
class HuntressOrganizationNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "id",
        description="Huntress-unique identifier for the organization.",
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    name: PropertyRef = PropertyRef(
        "name",
        extra_index=True,
        description="Public facing name for the organization.",
    )
    key: PropertyRef = PropertyRef(
        "key",
        extra_index=True,
        description="Subdomain associated with the organization.",
    )
    agents_count: PropertyRef = PropertyRef(
        "agents_count",
        description="Number of agents deployed for the organization.",
    )
    incident_reports_count: PropertyRef = PropertyRef(
        "incident_reports_count",
        description="Number of incident reports raised for the organization.",
    )
    identity_provider_tenant_id: PropertyRef = PropertyRef(
        "identity_provider_tenant_id",
        extra_index=True,
        description=(
            "Identity provider tenant ID associated with the organization, which "
            "ties it to the Entra or Google Workspace tenant it protects."
        ),
    )
    created_at: PropertyRef = PropertyRef(
        "created_at",
        description="Timestamp when the organization was created.",
    )
    updated_at: PropertyRef = PropertyRef(
        "updated_at",
        description="Timestamp when the organization was last updated.",
    )


@dataclass(frozen=True)
class HuntressOrganizationToAccountRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


# (:HuntressAccount)-[:RESOURCE]->(:HuntressOrganization)
@dataclass(frozen=True)
class HuntressOrganizationToAccountRel(CartographyRelSchema):
    """Links a Huntress account to one of its organizations."""

    target_node_label: str = "HuntressAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("ACCOUNT_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: HuntressOrganizationToAccountRelProperties = (
        HuntressOrganizationToAccountRelProperties()
    )


@dataclass(frozen=True)
class HuntressOrganizationSchema(CartographyNodeSchema):
    """A customer organization managed under a Huntress account."""

    label: str = "HuntressOrganization"
    properties: HuntressOrganizationNodeProperties = (
        HuntressOrganizationNodeProperties()
    )
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels([TENANT])
    sub_resource_relationship: HuntressOrganizationToAccountRel = (
        HuntressOrganizationToAccountRel()
    )

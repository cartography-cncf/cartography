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


@dataclass(frozen=True)
class WorkOSOrganizationNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id", description="WorkOS organization ID.")
    name: PropertyRef = PropertyRef("name", description="Organization name.")
    created_at: PropertyRef = PropertyRef(
        "created_at",
        description="RFC 3339 timestamp when the organization was created.",
    )
    updated_at: PropertyRef = PropertyRef(
        "updated_at",
        description="RFC 3339 timestamp when the organization was updated.",
    )
    allow_profiles_outside_organization: PropertyRef = PropertyRef(
        "allow_profiles_outside_organization",
        description="Whether profiles outside the organization are allowed.",
    )
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated", set_in_kwargs=True, description="Timestamp of the last update."
    )


@dataclass(frozen=True)
class WorkOSOrganizationToEnvironmentRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:WorkOSEnvironment)-[:RESOURCE]->(:WorkOSOrganization)
class WorkOSOrganizationToEnvironmentRel(CartographyRelSchema):
    """The WorkOS environment contains this organization as a resource."""

    target_node_label: str = "WorkOSEnvironment"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("WORKOS_CLIENT_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: WorkOSOrganizationToEnvironmentRelProperties = (
        WorkOSOrganizationToEnvironmentRelProperties()
    )


@dataclass(frozen=True)
class WorkOSOrganizationSchema(CartographyNodeSchema):
    """A WorkOS organization with the canonical Tenant label."""

    label: str = "WorkOSOrganization"
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(["Tenant"])
    properties: WorkOSOrganizationNodeProperties = WorkOSOrganizationNodeProperties()
    sub_resource_relationship: WorkOSOrganizationToEnvironmentRel = (
        WorkOSOrganizationToEnvironmentRel()
    )

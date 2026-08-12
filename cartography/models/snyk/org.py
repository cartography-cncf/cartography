from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.nodes import ExtraNodeLabels
from cartography.models.ontology.labels import TENANT


@dataclass(frozen=True)
class SnykOrgNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id", description="ID of the Snyk organization.")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    name: PropertyRef = PropertyRef(
        "name", extra_index=True, description="Display name of the Snyk organization."
    )
    slug: PropertyRef = PropertyRef(
        "slug", description="URL slug for the organization."
    )
    group_id: PropertyRef = PropertyRef(
        "group_id", description="ID of the Snyk group containing this organization."
    )


@dataclass(frozen=True)
class SnykOrgSchema(CartographyNodeSchema):
    """A Snyk organization, the tenant boundary for targets, projects, and issues."""

    label: str = "SnykOrg"
    properties: SnykOrgNodeProperties = SnykOrgNodeProperties()
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels([TENANT])

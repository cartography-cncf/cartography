from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.nodes import ExtraNodeLabels
from cartography.models.ontology.labels import TENANT


@dataclass(frozen=True)
class PylonOrganizationNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id", description="Pylon organization ID.")
    name: PropertyRef = PropertyRef("name", description="Organization name.")
    base_url: PropertyRef = PropertyRef(
        "base_url",
        description=(
            "Pylon API base URL that the organization was read from, which "
            "identifies its region (US or EU)."
        ),
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class PylonOrganizationSchema(CartographyNodeSchema):
    """A Pylon organization (workspace), read from the `GET /me` endpoint.

    The organization is the tenant for every other Pylon node. Cartography
    reads only workspace identity and access data: users, API token
    identities and bots, roles, and teams.
    It doesn't read customer data such as accounts, contacts, or issues.
    """

    label: str = "PylonOrganization"
    properties: PylonOrganizationNodeProperties = PylonOrganizationNodeProperties()
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels([TENANT])

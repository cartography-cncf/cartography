from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.nodes import ExtraNodeLabels
from cartography.models.ontology.labels import TENANT


@dataclass(frozen=True)
class RenderTenantNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id", description="ID of the Render workspace.")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    name: PropertyRef = PropertyRef(
        "name", extra_index=True, description="Display name of the workspace."
    )
    email: PropertyRef = PropertyRef(
        "email", description="Email address associated with the workspace."
    )
    type: PropertyRef = PropertyRef(
        "type", description="Workspace type: `user` (personal) or `team`."
    )


@dataclass(frozen=True)
class RenderTenantSchema(CartographyNodeSchema):
    """
    A Render workspace (`owner`): the billing, ownership, and access boundary for every
    other Render resource.

    This has no sub_resource_relationship (a workspace is the root of the hierarchy) and
    no other_relationships, so its generated cleanup job is a deliberate no-op (see
    cleanupbuilder.build_cleanup_queries's early return for nodes with neither). A
    workspace the configured API key can no longer list - because access was revoked, not
    necessarily because the workspace was deleted - is therefore never marked stale, and
    start_render_ingestion() never re-visits it to clean its children either. Render API
    visibility is credential-dependent, so "access lost" and "resource deleted" are
    different things; conflating them would risk a temporarily misconfigured key wiping
    real graph history.
    """

    label: str = "RenderTenant"
    properties: RenderTenantNodeProperties = RenderTenantNodeProperties()
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels([TENANT])

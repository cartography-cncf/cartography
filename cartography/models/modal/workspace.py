from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.nodes import ExtraNodeLabels
from cartography.models.ontology.labels import TENANT


@dataclass(frozen=True)
class ModalWorkspaceNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    name: PropertyRef = PropertyRef("name", extra_index=True)
    # URL slug of the workspace. Web endpoint hostnames embed it, so it is the join key
    # between a ModalFunction.web_url and its workspace.
    slug: PropertyRef = PropertyRef("slug", extra_index=True)
    # Which credential performed the sync. Modal has no read-only token scope, so a
    # workspace inventoried with someone's personal token is a materially different
    # posture from one using a dedicated least-privilege service user, and it should be
    # queryable rather than buried in logs.
    synced_with_token_id: PropertyRef = PropertyRef("synced_with_token_id")
    synced_with_token_name: PropertyRef = PropertyRef("synced_with_token_name")
    # "user" or "service_user".
    synced_with_principal_type: PropertyRef = PropertyRef(
        "synced_with_principal_type", extra_index=True
    )
    synced_with_principal_id: PropertyRef = PropertyRef("synced_with_principal_id")
    synced_with_principal_name: PropertyRef = PropertyRef("synced_with_principal_name")
    synced_with_token_expires_at: PropertyRef = PropertyRef(
        "synced_with_token_expires_at"
    )


@dataclass(frozen=True)
# The workspace is the root of the Modal hierarchy and is derived from the API token
# itself, so it has no sub-resource relationship. It also declares no
# other_relationships, which means the cleanup builder produces no queries at all and
# no cleanup job is ever run for it. That is deliberate: a global cleanup would delete
# a sibling workspace ingested by a second token in the same graph.
class ModalWorkspaceSchema(CartographyNodeSchema):
    label: str = "ModalWorkspace"
    properties: ModalWorkspaceNodeProperties = ModalWorkspaceNodeProperties()
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels([TENANT])

from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.nodes import ExtraNodeLabels
from cartography.models.ontology.labels import TENANT


@dataclass(frozen=True)
class ModalWorkspaceNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "id", description="Workspace ID, e.g. `ac-DyLbE2VtEfgvSEhzMQAOcP`."
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    name: PropertyRef = PropertyRef(
        "name", extra_index=True, description="Workspace display name."
    )
    # URL slug of the workspace. Web endpoint hostnames embed it, so it is the join key
    # between a ModalFunction.web_url and its workspace.
    slug: PropertyRef = PropertyRef(
        "slug",
        extra_index=True,
        description="Workspace URL slug. Web endpoint hostnames embed it.",
    )
    # Which credential performed the sync. Modal has no read-only token scope, so a
    # workspace inventoried with someone's personal token is a materially different
    # posture from one using a dedicated least-privilege service user, and it should be
    # queryable rather than buried in logs.
    synced_with_token_id: PropertyRef = PropertyRef(
        "synced_with_token_id",
        description="ID of the API token that performed the sync.",
    )
    synced_with_token_name: PropertyRef = PropertyRef(
        "synced_with_token_name", description="Name of that token."
    )
    # "user" or "service_user".
    synced_with_principal_type: PropertyRef = PropertyRef(
        "synced_with_principal_type",
        extra_index=True,
        description="`user` or `service_user`. Modal has no read-only token scope, so this records how privileged the sync credential was.",
    )
    synced_with_principal_id: PropertyRef = PropertyRef(
        "synced_with_principal_id",
        description="ID of the user or service user that owns the sync token.",
    )
    synced_with_principal_name: PropertyRef = PropertyRef(
        "synced_with_principal_name", description="Name of that principal."
    )
    synced_with_token_expires_at: PropertyRef = PropertyRef(
        "synced_with_token_expires_at",
        description="Token expiry, if any. Modal API tokens do not normally expire.",
    )


@dataclass(frozen=True)
# The workspace is the root of the Modal hierarchy and is derived from the API token
# itself, so it has no sub-resource relationship. It also declares no
# other_relationships, which means the cleanup builder produces no queries at all and
# no cleanup job is ever run for it. That is deliberate: a global cleanup would delete
# a sibling workspace ingested by a second token in the same graph.
class ModalWorkspaceSchema(CartographyNodeSchema):
    """Represents a Modal workspace, the top of the Modal hierarchy. One workspace is derived from the API token used to sync, via `TokenInfoGet`. Because a workspace is derived from the credential rather than enumerated, this node has no sub-resource relationship and is never subject to a cleanup job: deleting it globally would remove a sibling workspace ingested by a second token into the same graph."""

    label: str = "ModalWorkspace"
    properties: ModalWorkspaceNodeProperties = ModalWorkspaceNodeProperties()
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels([TENANT])

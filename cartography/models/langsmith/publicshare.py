from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.relationships import CartographyRelProperties
from cartography.models.core.relationships import CartographyRelSchema
from cartography.models.core.relationships import LinkDirection
from cartography.models.core.relationships import make_target_node_matcher
from cartography.models.core.relationships import TargetNodeMatcher


@dataclass(frozen=True)
class LangSmithPublicShareNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "id",
        description=(
            "Synthetic identifier of the form <share_type>|<entity_id>. The share token, "
            "which is the public URL's credential, is never ingested."
        ),
    )
    share_type: PropertyRef = PropertyRef(
        "share_type",
        extra_index=True,
        description="What is exposed: run, dataset, thread, or repo.",
    )
    entity_id: PropertyRef = PropertyRef(
        "entity_id",
        description="ID of the shared run, dataset, thread, or repo.",
    )
    entity_name: PropertyRef = PropertyRef(
        "entity_name", description="Name of the shared entity, when LangSmith has one."
    )
    repo_type: PropertyRef = PropertyRef(
        "repo_type",
        description="For a public repo, whether it holds a prompt or an agent.",
    )
    project_id: PropertyRef = PropertyRef(
        "project_id",
        description="UUID of the tracing project a shared run or thread is in.",
    )
    project_name: PropertyRef = PropertyRef(
        "project_name",
        description="Name of the tracing project a shared run or thread is in.",
    )
    created_at: PropertyRef = PropertyRef(
        "created_at", description="Timestamp when the entity was shared."
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class LangSmithPublicShareToWorkspaceRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:LangSmithWorkspace)-[:RESOURCE]->(:LangSmithPublicShare)
class LangSmithPublicShareToWorkspaceRel(CartographyRelSchema):
    """Links a public share to the workspace it belongs to."""

    target_node_label: str = "LangSmithWorkspace"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("WORKSPACE_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: LangSmithPublicShareToWorkspaceRelProperties = (
        LangSmithPublicShareToWorkspaceRelProperties()
    )


@dataclass(frozen=True)
class LangSmithPublicShareSchema(CartographyNodeSchema):
    """
    A run, dataset, thread, or prompt or agent repo that anyone with the link can read,
    without a LangSmith account. A shared dataset also exposes its experiments and runs.
    """

    label: str = "LangSmithPublicShare"
    properties: LangSmithPublicShareNodeProperties = (
        LangSmithPublicShareNodeProperties()
    )
    sub_resource_relationship: LangSmithPublicShareToWorkspaceRel = (
        LangSmithPublicShareToWorkspaceRel()
    )

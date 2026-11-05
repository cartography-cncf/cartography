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
from cartography.models.ontology.labels import SECRET


@dataclass(frozen=True)
class LangSmithSecretNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "id", description="Synthetic identifier of the form <workspace_id>|<key>."
    )
    name: PropertyRef = PropertyRef(
        "key",
        extra_index=True,
        description="Secret key name. The secret value is never ingested.",
    )
    workspace_id: PropertyRef = PropertyRef(
        "workspace_id", description="UUID of the workspace holding the secret."
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class LangSmithSecretToWorkspaceRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:LangSmithWorkspace)-[:RESOURCE]->(:LangSmithSecret)
class LangSmithSecretToWorkspaceRel(CartographyRelSchema):
    """Links a workspace secret to the workspace it belongs to."""

    target_node_label: str = "LangSmithWorkspace"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("WORKSPACE_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: LangSmithSecretToWorkspaceRelProperties = (
        LangSmithSecretToWorkspaceRelProperties()
    )


@dataclass(frozen=True)
class LangSmithSecretSchema(CartographyNodeSchema):
    """
    A workspace secret. Cartography ingests only the key name and never calls LangSmith's
    encrypted-secrets endpoint.
    """

    label: str = "LangSmithSecret"
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(
        [SECRET]
    )  # Secret label is used for ontology mapping
    properties: LangSmithSecretNodeProperties = LangSmithSecretNodeProperties()
    sub_resource_relationship: LangSmithSecretToWorkspaceRel = (
        LangSmithSecretToWorkspaceRel()
    )

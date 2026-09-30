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
class LangSmithSecretToOrganizationRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:LangSmithOrganization)-[:RESOURCE]->(:LangSmithSecret)
class LangSmithSecretToOrganizationRel(CartographyRelSchema):
    """Links an organization to a workspace secret held within it."""

    target_node_label: str = "LangSmithOrganization"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("ORG_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: LangSmithSecretToOrganizationRelProperties = (
        LangSmithSecretToOrganizationRelProperties()
    )


@dataclass(frozen=True)
class LangSmithSecretToWorkspaceRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:LangSmithWorkspace)-[:CONTAINS]->(:LangSmithSecret)
class LangSmithSecretToWorkspaceRel(CartographyRelSchema):
    """Links a secret to the workspace that holds it."""

    target_node_label: str = "LangSmithWorkspace"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("workspace_id")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "CONTAINS"
    properties: LangSmithSecretToWorkspaceRelProperties = (
        LangSmithSecretToWorkspaceRelProperties()
    )


@dataclass(frozen=True)
class LangSmithSecretSchema(CartographyNodeSchema):
    """
    A workspace secret. Only the key name is ingested; LangSmith's encrypted-secrets endpoint
    is never called.
    """

    label: str = "LangSmithSecret"
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(
        [SECRET]
    )  # Secret label is used for ontology mapping
    properties: LangSmithSecretNodeProperties = LangSmithSecretNodeProperties()
    sub_resource_relationship: LangSmithSecretToOrganizationRel = (
        LangSmithSecretToOrganizationRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            LangSmithSecretToWorkspaceRel(),
        ],
    )

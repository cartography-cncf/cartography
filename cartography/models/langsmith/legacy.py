"""
Ownership edges that earlier versions of the LangSmith module wrote.

Workspace resources used to hang off the organization through RESOURCE, and some off
their workspace through CONTAINS or IN_WORKSPACE. Cleanup reaches a node only through its
schema's sub-resource edge, so these shapes let it remove the old edges, and the nodes
deleted upstream before the upgrade, from graphs those versions built.

DEPRECATED: this migration will be removed in v1.0.0.
"""

from dataclasses import dataclass
from typing import ClassVar

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.relationships import CartographyRelProperties
from cartography.models.core.relationships import CartographyRelSchema
from cartography.models.core.relationships import LinkDirection
from cartography.models.core.relationships import make_target_node_matcher
from cartography.models.core.relationships import TargetNodeMatcher


@dataclass(frozen=True)
class LangSmithLegacyRelProperties(CartographyRelProperties):
    __cartography_introspection_exclude__: ClassVar[bool] = True

    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:LangSmithOrganization)-[:RESOURCE]->(n)
class LangSmithLegacyOrganizationRel(CartographyRelSchema):
    """The organization ownership edge earlier versions wrote for workspace resources."""

    __cartography_introspection_exclude__: ClassVar[bool] = True

    target_node_label: str = "LangSmithOrganization"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("ORG_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: LangSmithLegacyRelProperties = LangSmithLegacyRelProperties()


@dataclass(frozen=True)
# (:LangSmithWorkspace)-[:CONTAINS]->(n)
class LangSmithLegacyWorkspaceContainsRel(CartographyRelSchema):
    """The workspace edge earlier versions wrote for deployments and workspace resources."""

    __cartography_introspection_exclude__: ClassVar[bool] = True

    target_node_label: str = "LangSmithWorkspace"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("WORKSPACE_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "CONTAINS"
    properties: LangSmithLegacyRelProperties = LangSmithLegacyRelProperties()


@dataclass(frozen=True)
# (n)-[:IN_WORKSPACE]->(:LangSmithWorkspace)
class LangSmithLegacyInWorkspaceRel(CartographyRelSchema):
    """The workspace edge earlier versions wrote for workspace memberships."""

    __cartography_introspection_exclude__: ClassVar[bool] = True

    target_node_label: str = "LangSmithWorkspace"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("WORKSPACE_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "IN_WORKSPACE"
    properties: LangSmithLegacyRelProperties = LangSmithLegacyRelProperties()


@dataclass(frozen=True)
class LangSmithLegacyNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class LangSmithLegacyOwnershipCleanupSchema(CartographyNodeSchema):
    """Reaches a schema's nodes through an ownership edge earlier versions wrote."""

    __cartography_introspection_exclude__: ClassVar[bool] = True

    # Callers name the label of the schema whose earlier shape they clean up. A default
    # is required only so the dataclass field overrides the abstract property.
    label: str = ""
    sub_resource_relationship: CartographyRelSchema = LangSmithLegacyOrganizationRel()
    properties: LangSmithLegacyNodeProperties = LangSmithLegacyNodeProperties()

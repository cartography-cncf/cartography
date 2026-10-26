from dataclasses import dataclass
from typing import ClassVar

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.nodes import ExtraNodeLabels
from cartography.models.core.relationships import CartographyRelProperties
from cartography.models.core.relationships import CartographyRelSchema
from cartography.models.core.relationships import LinkDirection
from cartography.models.core.relationships import make_source_node_matcher
from cartography.models.core.relationships import make_target_node_matcher
from cartography.models.core.relationships import SourceNodeMatcher
from cartography.models.core.relationships import TargetNodeMatcher
from cartography.models.ontology.labels import TENANT


@dataclass(frozen=True)
class DatabricksWorkspaceNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "id",
        description="Numeric Databricks workspace ID.",
    )
    workspace_id: PropertyRef = PropertyRef(
        "workspace_id",
        extra_index=True,
        description="Numeric Databricks workspace ID.",
    )
    host: PropertyRef = PropertyRef(
        "host",
        extra_index=True,
        description="Full URL of the Databricks workspace.",
    )
    tokens_enabled: PropertyRef = PropertyRef(
        "tokens_enabled",
        description="Whether personal access tokens are enabled in the workspace.",
    )
    max_token_lifetime_days: PropertyRef = PropertyRef(
        "max_token_lifetime_days",
        description="Maximum personal access token lifetime in days.",
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


# The workspace API and the account API each see part of a workspace. Each path
# loads its own schema over the DatabricksWorkspace label and writes only the
# properties it reads, so neither nulls out what the other set.
@dataclass(frozen=True)
class DatabricksAccountWorkspaceNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "id",
        description="Numeric Databricks workspace ID.",
    )
    workspace_id: PropertyRef = PropertyRef(
        "workspace_id",
        extra_index=True,
        description="Numeric Databricks workspace ID.",
    )
    deployment_name: PropertyRef = PropertyRef(
        "deployment_name",
        description="Workspace deployment name used in its host name.",
    )
    workspace_name: PropertyRef = PropertyRef(
        "workspace_name",
        description="Workspace display name.",
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class DatabricksWorkspaceToAccountRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:DatabricksAccount)-[:RESOURCE]->(:DatabricksWorkspace)
class DatabricksWorkspaceToAccountRel(CartographyRelSchema):
    """A Databricks account owns a workspace."""

    target_node_label: str = "DatabricksAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("ACCOUNT_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: DatabricksWorkspaceToAccountRelProperties = (
        DatabricksWorkspaceToAccountRelProperties()
    )


@dataclass(frozen=True)
class DatabricksAccountToWorkspaceRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    _sub_resource_label: PropertyRef = PropertyRef(
        "_sub_resource_label", set_in_kwargs=True
    )
    _sub_resource_id: PropertyRef = PropertyRef("_sub_resource_id", set_in_kwargs=True)


@dataclass(frozen=True)
# (:DatabricksAccount)-[:RESOURCE]->(:DatabricksWorkspace)
# The workspace path's copy of the account edge, as a MatchLink scoped to the
# account: the workspace-only path has no account to anchor the node to.
class DatabricksAccountToWorkspaceRel(CartographyRelSchema):
    """A Databricks account owns a workspace."""

    source_node_label: str = "DatabricksAccount"
    source_node_matcher: SourceNodeMatcher = make_source_node_matcher(
        {"id": PropertyRef("ACCOUNT_ID", set_in_kwargs=True)},
    )
    target_node_label: str = "DatabricksWorkspace"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("id")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "RESOURCE"
    properties: DatabricksAccountToWorkspaceRelProperties = (
        DatabricksAccountToWorkspaceRelProperties()
    )


@dataclass(frozen=True)
class DatabricksWorkspaceSchema(CartographyNodeSchema):
    """A Databricks workspace identified by its host, as its own API reports it."""

    label: str = "DatabricksWorkspace"
    properties: DatabricksWorkspaceNodeProperties = DatabricksWorkspaceNodeProperties()
    # `Tenant` is the ontology label for the top-level resource container.
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels([TENANT])


@dataclass(frozen=True)
class DatabricksAccountWorkspaceSchema(CartographyNodeSchema):
    """A Databricks workspace as the account API reports it.

    Anchored to the account, so a workspace the account stops listing is
    deleted with its resources when the account is cleaned up.
    """

    label: str = "DatabricksWorkspace"
    properties: DatabricksAccountWorkspaceNodeProperties = (
        DatabricksAccountWorkspaceNodeProperties()
    )
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels([TENANT])
    sub_resource_relationship: DatabricksWorkspaceToAccountRel = (
        DatabricksWorkspaceToAccountRel()
    )


# DEPRECATED: migration of the host-keyed DatabricksWorkspace nodes earlier
# versions created will be removed in v1.0.0. The workspace path links the
# numeric-id node to the host-keyed one with RESOURCE, so a cascading cleanup
# scoped to the numeric id deletes the old node and everything under it. In
# account mode the account cleanup already removes them, since the account no
# longer lists them.
@dataclass(frozen=True)
class LegacyHostKeyedWorkspaceRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    _sub_resource_label: PropertyRef = PropertyRef(
        "_sub_resource_label", set_in_kwargs=True
    )
    _sub_resource_id: PropertyRef = PropertyRef("_sub_resource_id", set_in_kwargs=True)


@dataclass(frozen=True)
class LegacyHostKeyedWorkspaceRel(CartographyRelSchema):
    __cartography_introspection_exclude__: ClassVar[bool] = True

    source_node_label: str = "DatabricksWorkspace"
    source_node_matcher: SourceNodeMatcher = make_source_node_matcher(
        {"id": PropertyRef("WORKSPACE_ID", set_in_kwargs=True)},
    )
    target_node_label: str = "DatabricksWorkspace"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("legacy_id")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "RESOURCE"
    properties: LegacyHostKeyedWorkspaceRelProperties = (
        LegacyHostKeyedWorkspaceRelProperties()
    )


@dataclass(frozen=True)
class LegacyHostKeyedWorkspaceNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class LegacyHostKeyedWorkspaceParentRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class LegacyHostKeyedWorkspaceParentRel(CartographyRelSchema):
    __cartography_introspection_exclude__: ClassVar[bool] = True

    target_node_label: str = "DatabricksWorkspace"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("WORKSPACE_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: LegacyHostKeyedWorkspaceParentRelProperties = (
        LegacyHostKeyedWorkspaceParentRelProperties()
    )


@dataclass(frozen=True)
class LegacyHostKeyedWorkspaceCleanupSchema(CartographyNodeSchema):
    __cartography_introspection_exclude__: ClassVar[bool] = True

    label: str = "DatabricksWorkspace"
    properties: LegacyHostKeyedWorkspaceNodeProperties = (
        LegacyHostKeyedWorkspaceNodeProperties()
    )
    sub_resource_relationship: LegacyHostKeyedWorkspaceParentRel = (
        LegacyHostKeyedWorkspaceParentRel()
    )

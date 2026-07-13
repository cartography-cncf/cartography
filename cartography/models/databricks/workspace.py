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


@dataclass(frozen=True)
class DatabricksWorkspaceNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id")
    host: PropertyRef = PropertyRef("host", extra_index=True)
    tokens_enabled: PropertyRef = PropertyRef("tokens_enabled")
    max_token_lifetime_days: PropertyRef = PropertyRef("max_token_lifetime_days")
    # Numeric account-API workspace id + deployment/name, set by the account
    # workspaces sync when account creds are configured (None on the
    # workspace-only path). Lets workspace permission assignments key off the
    # numeric id the account API reports.
    workspace_id: PropertyRef = PropertyRef("workspace_id", extra_index=True)
    deployment_name: PropertyRef = PropertyRef("deployment_name")
    workspace_name: PropertyRef = PropertyRef("workspace_name")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class DatabricksWorkspaceToAccountRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:DatabricksAccount)-[:RESOURCE]->(:DatabricksWorkspace)
class DatabricksWorkspaceToAccountRel(CartographyRelSchema):
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
class DatabricksWorkspaceSchema(CartographyNodeSchema):
    label: str = "DatabricksWorkspace"
    properties: DatabricksWorkspaceNodeProperties = DatabricksWorkspaceNodeProperties()
    # `Tenant` is the ontology label for the top-level resource container.
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(["Tenant"])
    # The account owns the workspace. Modelled as a plain relationship (not the
    # sub-resource relationship) so the workspace-only path keeps working: when
    # no account creds are configured, ACCOUNT_ID is None, the account node is
    # absent, and this edge simply does not form. Workspace cleanup stays global.
    other_relationships: OtherRelationships = OtherRelationships(
        [DatabricksWorkspaceToAccountRel()],
    )

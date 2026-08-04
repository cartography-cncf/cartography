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
from cartography.models.databricks.extra_labels import DATABRICKS_ACL_OBJECT


@dataclass(frozen=True)
class DatabricksClusterPolicyNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "id", description="Workspace-scoped identifier for the cluster policy."
    )
    policy_id: PropertyRef = PropertyRef(
        "policy_id",
        extra_index=True,
        description="Databricks cluster policy identifier.",
    )
    name: PropertyRef = PropertyRef(
        "name", extra_index=True, description="Name of the cluster policy."
    )
    description: PropertyRef = PropertyRef(
        "description", description="Description of the cluster policy."
    )
    definition: PropertyRef = PropertyRef(
        "definition", description="JSON definition of the cluster policy."
    )
    policy_family_id: PropertyRef = PropertyRef(
        "policy_family_id",
        description="Identifier of the policy family used by this policy.",
    )
    creator_user_name: PropertyRef = PropertyRef(
        "creator_user_name",
        extra_index=True,
        description="User who created the cluster policy.",
    )
    created_at: PropertyRef = PropertyRef(
        "created_at", description="Timestamp when the cluster policy was created."
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class DatabricksClusterPolicyToWorkspaceRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:DatabricksWorkspace)-[:RESOURCE]->(:DatabricksClusterPolicy)
class DatabricksClusterPolicyToWorkspaceRel(CartographyRelSchema):
    """A Databricks workspace contains the cluster policy as a resource."""

    target_node_label: str = "DatabricksWorkspace"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("WORKSPACE_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: DatabricksClusterPolicyToWorkspaceRelProperties = (
        DatabricksClusterPolicyToWorkspaceRelProperties()
    )


@dataclass(frozen=True)
class DatabricksClusterPolicySchema(CartographyNodeSchema):
    """A Databricks policy that constrains cluster configuration."""

    label: str = "DatabricksClusterPolicy"
    properties: DatabricksClusterPolicyNodeProperties = (
        DatabricksClusterPolicyNodeProperties()
    )
    sub_resource_relationship: DatabricksClusterPolicyToWorkspaceRel = (
        DatabricksClusterPolicyToWorkspaceRel()
    )
    # ACL-target ontology label so the HAS_PERMISSION MatchLinks can target it.
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels([DATABRICKS_ACL_OBJECT])

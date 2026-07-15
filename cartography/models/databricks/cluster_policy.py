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


@dataclass(frozen=True)
class DatabricksClusterPolicyNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id")
    policy_id: PropertyRef = PropertyRef("policy_id", extra_index=True)
    name: PropertyRef = PropertyRef("name", extra_index=True)
    description: PropertyRef = PropertyRef("description")
    definition: PropertyRef = PropertyRef("definition")
    policy_family_id: PropertyRef = PropertyRef("policy_family_id")
    creator_user_name: PropertyRef = PropertyRef("creator_user_name", extra_index=True)
    created_at: PropertyRef = PropertyRef("created_at")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class DatabricksClusterPolicyToWorkspaceRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:DatabricksWorkspace)-[:RESOURCE]->(:DatabricksClusterPolicy)
class DatabricksClusterPolicyToWorkspaceRel(CartographyRelSchema):
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
    label: str = "DatabricksClusterPolicy"
    properties: DatabricksClusterPolicyNodeProperties = (
        DatabricksClusterPolicyNodeProperties()
    )
    sub_resource_relationship: DatabricksClusterPolicyToWorkspaceRel = (
        DatabricksClusterPolicyToWorkspaceRel()
    )
    # ACL-target ontology label so the HAS_PERMISSION MatchLinks can target it.
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(["DatabricksAclObject"])

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
from cartography.models.ontology.labels import SERVICE_ACCOUNT


@dataclass(frozen=True)
class DatabricksServicePrincipalNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "id", description="Workspace-scoped identifier for the service principal."
    )
    scim_id: PropertyRef = PropertyRef(
        "scim_id",
        extra_index=True,
        description="Databricks SCIM service principal identifier.",
    )
    application_id: PropertyRef = PropertyRef(
        "application_id",
        extra_index=True,
        description="Application identifier of the service principal.",
    )
    display_name: PropertyRef = PropertyRef(
        "display_name", description="Display name of the service principal."
    )
    external_id: PropertyRef = PropertyRef(
        "external_id",
        description="Identifier assigned by the external identity provider.",
    )
    active: PropertyRef = PropertyRef(
        "active", description="Whether the service principal is active."
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class DatabricksServicePrincipalToWorkspaceRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:DatabricksWorkspace)-[:RESOURCE]->(:DatabricksServicePrincipal)
class DatabricksServicePrincipalToWorkspaceRel(CartographyRelSchema):
    """A Databricks workspace contains the service principal as a resource."""

    target_node_label: str = "DatabricksWorkspace"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("WORKSPACE_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: DatabricksServicePrincipalToWorkspaceRelProperties = (
        DatabricksServicePrincipalToWorkspaceRelProperties()
    )


@dataclass(frozen=True)
class DatabricksServicePrincipalToGroupRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:DatabricksServicePrincipal)-[:MEMBER_OF]->(:DatabricksGroup)
class DatabricksServicePrincipalToGroupRel(CartographyRelSchema):
    """A Databricks principal is a member of a Databricks group."""

    target_node_label: str = "DatabricksGroup"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("group_ids", one_to_many=True)},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "MEMBER_OF"
    properties: DatabricksServicePrincipalToGroupRelProperties = (
        DatabricksServicePrincipalToGroupRelProperties()
    )


@dataclass(frozen=True)
class DatabricksServicePrincipalSchema(CartographyNodeSchema):
    """A nonhuman identity in a Databricks workspace."""

    label: str = "DatabricksServicePrincipal"
    properties: DatabricksServicePrincipalNodeProperties = (
        DatabricksServicePrincipalNodeProperties()
    )
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels([SERVICE_ACCOUNT])
    sub_resource_relationship: DatabricksServicePrincipalToWorkspaceRel = (
        DatabricksServicePrincipalToWorkspaceRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [DatabricksServicePrincipalToGroupRel()],
    )

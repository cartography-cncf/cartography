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
class DatabricksAccountServicePrincipalNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "id",
        description="Account-scoped Databricks SCIM service principal ID.",
    )
    scim_id: PropertyRef = PropertyRef(
        "scim_id",
        extra_index=True,
        description="Databricks account SCIM service principal ID.",
    )
    application_id: PropertyRef = PropertyRef(
        "application_id",
        extra_index=True,
        description="OAuth application ID for the service principal.",
    )
    display_name: PropertyRef = PropertyRef(
        "display_name",
        description="Service principal display name.",
    )
    external_id: PropertyRef = PropertyRef(
        "external_id",
        description="External identity provider ID for the service principal.",
    )
    active: PropertyRef = PropertyRef(
        "active",
        description="Whether the service principal is active.",
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class DatabricksAccountServicePrincipalToAccountRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:DatabricksAccount)-[:RESOURCE]->(:DatabricksAccountServicePrincipal)
class DatabricksAccountServicePrincipalToAccountRel(CartographyRelSchema):
    """A Databricks account owns an account-level resource."""

    target_node_label: str = "DatabricksAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("ACCOUNT_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: DatabricksAccountServicePrincipalToAccountRelProperties = (
        DatabricksAccountServicePrincipalToAccountRelProperties()
    )


@dataclass(frozen=True)
class DatabricksAccountServicePrincipalToGroupRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:DatabricksAccountServicePrincipal)-[:MEMBER_OF]->(:DatabricksAccountGroup)
class DatabricksAccountServicePrincipalToGroupRel(CartographyRelSchema):
    """A Databricks account service principal is a member of an account group."""

    target_node_label: str = "DatabricksAccountGroup"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("group_ids", one_to_many=True)},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "MEMBER_OF"
    properties: DatabricksAccountServicePrincipalToGroupRelProperties = (
        DatabricksAccountServicePrincipalToGroupRelProperties()
    )


@dataclass(frozen=True)
class DatabricksAccountServicePrincipalSchema(CartographyNodeSchema):
    """A Databricks account-level SCIM service principal."""

    label: str = "DatabricksAccountServicePrincipal"
    properties: DatabricksAccountServicePrincipalNodeProperties = (
        DatabricksAccountServicePrincipalNodeProperties()
    )
    # `ServiceAccount` matches the workspace-level DatabricksServicePrincipal so
    # both surface under the same ontology label for cross-provider queries.
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels([SERVICE_ACCOUNT])
    sub_resource_relationship: DatabricksAccountServicePrincipalToAccountRel = (
        DatabricksAccountServicePrincipalToAccountRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [DatabricksAccountServicePrincipalToGroupRel()],
    )

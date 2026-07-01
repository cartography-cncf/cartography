from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.relationships import CartographyRelProperties
from cartography.models.core.relationships import CartographyRelSchema
from cartography.models.core.relationships import LinkDirection
from cartography.models.core.relationships import make_source_node_matcher
from cartography.models.core.relationships import make_target_node_matcher
from cartography.models.core.relationships import SourceNodeMatcher
from cartography.models.core.relationships import TargetNodeMatcher


@dataclass(frozen=True)
class DatabricksGrantRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    _sub_resource_label: PropertyRef = PropertyRef(
        "_sub_resource_label", set_in_kwargs=True
    )
    _sub_resource_id: PropertyRef = PropertyRef("_sub_resource_id", set_in_kwargs=True)
    privileges: PropertyRef = PropertyRef("privileges")


@dataclass(frozen=True)
# (:DatabricksUser)-[:HAS_PRIVILEGE {privileges}]->(:DatabricksSecurable)
# UC grants name the principal by username/email for users.
class DatabricksUserGrantRel(CartographyRelSchema):
    target_node_label: str = "DatabricksSecurable"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("securable_id")},
    )
    source_node_label: str = "DatabricksUser"
    source_node_matcher: SourceNodeMatcher = make_source_node_matcher(
        {"user_name": PropertyRef("principal")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "HAS_PRIVILEGE"
    properties: DatabricksGrantRelProperties = DatabricksGrantRelProperties()


@dataclass(frozen=True)
# (:DatabricksGroup)-[:HAS_PRIVILEGE {privileges}]->(:DatabricksSecurable)
# UC grants name the principal by display name for groups.
class DatabricksGroupGrantRel(CartographyRelSchema):
    target_node_label: str = "DatabricksSecurable"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("securable_id")},
    )
    source_node_label: str = "DatabricksGroup"
    source_node_matcher: SourceNodeMatcher = make_source_node_matcher(
        {"display_name": PropertyRef("principal")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "HAS_PRIVILEGE"
    properties: DatabricksGrantRelProperties = DatabricksGrantRelProperties()


@dataclass(frozen=True)
# (:DatabricksServicePrincipal)-[:HAS_PRIVILEGE {privileges}]->(:DatabricksSecurable)
# UC grants name the principal by OAuth application id for service principals.
class DatabricksServicePrincipalGrantRel(CartographyRelSchema):
    target_node_label: str = "DatabricksSecurable"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("securable_id")},
    )
    source_node_label: str = "DatabricksServicePrincipal"
    source_node_matcher: SourceNodeMatcher = make_source_node_matcher(
        {"application_id": PropertyRef("principal")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "HAS_PRIVILEGE"
    properties: DatabricksGrantRelProperties = DatabricksGrantRelProperties()

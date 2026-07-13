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


# The three principal rels all match the source by ``principal_id`` — the
# workspace-scoped node id resolved from the grant's principal name in the intel
# layer. Matching by the scoped id (not the bare name) keeps grants from two
# workspaces that share an email / group name / application id from attaching to
# the wrong workspace's principal.


@dataclass(frozen=True)
# (:DatabricksUser)-[:HAS_PRIVILEGE {privileges}]->(:DatabricksSecurable)
class DatabricksUserGrantRel(CartographyRelSchema):
    target_node_label: str = "DatabricksSecurable"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("securable_id")},
    )
    source_node_label: str = "DatabricksUser"
    source_node_matcher: SourceNodeMatcher = make_source_node_matcher(
        {"id": PropertyRef("principal_id")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "HAS_PRIVILEGE"
    properties: DatabricksGrantRelProperties = DatabricksGrantRelProperties()


@dataclass(frozen=True)
# (:DatabricksGroup)-[:HAS_PRIVILEGE {privileges}]->(:DatabricksSecurable)
class DatabricksGroupGrantRel(CartographyRelSchema):
    target_node_label: str = "DatabricksSecurable"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("securable_id")},
    )
    source_node_label: str = "DatabricksGroup"
    source_node_matcher: SourceNodeMatcher = make_source_node_matcher(
        {"id": PropertyRef("principal_id")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "HAS_PRIVILEGE"
    properties: DatabricksGrantRelProperties = DatabricksGrantRelProperties()


@dataclass(frozen=True)
# (:DatabricksServicePrincipal)-[:HAS_PRIVILEGE {privileges}]->(:DatabricksSecurable)
class DatabricksServicePrincipalGrantRel(CartographyRelSchema):
    target_node_label: str = "DatabricksSecurable"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("securable_id")},
    )
    source_node_label: str = "DatabricksServicePrincipal"
    source_node_matcher: SourceNodeMatcher = make_source_node_matcher(
        {"id": PropertyRef("principal_id")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "HAS_PRIVILEGE"
    properties: DatabricksGrantRelProperties = DatabricksGrantRelProperties()

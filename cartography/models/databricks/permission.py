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
class DatabricksPermissionRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    _sub_resource_label: PropertyRef = PropertyRef(
        "_sub_resource_label", set_in_kwargs=True
    )
    _sub_resource_id: PropertyRef = PropertyRef("_sub_resource_id", set_in_kwargs=True)
    permission_level: PropertyRef = PropertyRef("permission_level")


# The three principal rels all match the source by ``principal_id`` — the
# workspace-scoped node id resolved from the ACL entry's principal name in the
# intel layer. Matching by the scoped id (not the bare name) keeps ACLs from two
# workspaces that share an email / group name / application id from attaching to
# the wrong workspace's principal. They target the shared ``DatabricksAclObject``
# label so one set of three MatchLinks covers every ACL-bearing object type
# (clusters, jobs, pipelines, secret scopes, ...), exactly like
# ``DatabricksSecurable`` does for UC grants.


@dataclass(frozen=True)
# (:DatabricksUser)-[:HAS_PERMISSION {permission_level}]->(:DatabricksAclObject)
class DatabricksUserPermissionRel(CartographyRelSchema):
    target_node_label: str = "DatabricksAclObject"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("object_id")},
    )
    source_node_label: str = "DatabricksUser"
    source_node_matcher: SourceNodeMatcher = make_source_node_matcher(
        {"id": PropertyRef("principal_id")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "HAS_PERMISSION"
    properties: DatabricksPermissionRelProperties = DatabricksPermissionRelProperties()


@dataclass(frozen=True)
# (:DatabricksGroup)-[:HAS_PERMISSION {permission_level}]->(:DatabricksAclObject)
class DatabricksGroupPermissionRel(CartographyRelSchema):
    target_node_label: str = "DatabricksAclObject"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("object_id")},
    )
    source_node_label: str = "DatabricksGroup"
    source_node_matcher: SourceNodeMatcher = make_source_node_matcher(
        {"id": PropertyRef("principal_id")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "HAS_PERMISSION"
    properties: DatabricksPermissionRelProperties = DatabricksPermissionRelProperties()


@dataclass(frozen=True)
# (:DatabricksServicePrincipal)-[:HAS_PERMISSION {permission_level}]->(:DatabricksAclObject)
class DatabricksServicePrincipalPermissionRel(CartographyRelSchema):
    target_node_label: str = "DatabricksAclObject"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("object_id")},
    )
    source_node_label: str = "DatabricksServicePrincipal"
    source_node_matcher: SourceNodeMatcher = make_source_node_matcher(
        {"id": PropertyRef("principal_id")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "HAS_PERMISSION"
    properties: DatabricksPermissionRelProperties = DatabricksPermissionRelProperties()

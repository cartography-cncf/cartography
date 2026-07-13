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
class DatabricksWorkspaceAssignmentRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    _sub_resource_label: PropertyRef = PropertyRef(
        "_sub_resource_label", set_in_kwargs=True
    )
    _sub_resource_id: PropertyRef = PropertyRef("_sub_resource_id", set_in_kwargs=True)
    permissions: PropertyRef = PropertyRef("permissions")


# The three principal rels all match the source by ``principal_id`` — the
# account-scoped node id resolved from the assignment's SCIM ``principal_id`` in
# the intel layer. Matching by the scoped id (not the bare name) keeps
# assignments from two accounts that share an email / group name / application id
# from attaching to the wrong account's principal. The target workspace is
# matched by its deployment-host node id resolved from the account workspace list.


@dataclass(frozen=True)
# (:DatabricksAccountUser)-[:ASSIGNED_TO {permissions}]->(:DatabricksWorkspace)
class DatabricksAccountUserWorkspaceAssignmentRel(CartographyRelSchema):
    target_node_label: str = "DatabricksWorkspace"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("workspace_node_id")},
    )
    source_node_label: str = "DatabricksAccountUser"
    source_node_matcher: SourceNodeMatcher = make_source_node_matcher(
        {"id": PropertyRef("principal_id")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "ASSIGNED_TO"
    properties: DatabricksWorkspaceAssignmentRelProperties = (
        DatabricksWorkspaceAssignmentRelProperties()
    )


@dataclass(frozen=True)
# (:DatabricksAccountGroup)-[:ASSIGNED_TO {permissions}]->(:DatabricksWorkspace)
class DatabricksAccountGroupWorkspaceAssignmentRel(CartographyRelSchema):
    target_node_label: str = "DatabricksWorkspace"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("workspace_node_id")},
    )
    source_node_label: str = "DatabricksAccountGroup"
    source_node_matcher: SourceNodeMatcher = make_source_node_matcher(
        {"id": PropertyRef("principal_id")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "ASSIGNED_TO"
    properties: DatabricksWorkspaceAssignmentRelProperties = (
        DatabricksWorkspaceAssignmentRelProperties()
    )


@dataclass(frozen=True)
# (:DatabricksAccountServicePrincipal)-[:ASSIGNED_TO {permissions}]->(:DatabricksWorkspace)
class DatabricksAccountServicePrincipalWorkspaceAssignmentRel(CartographyRelSchema):
    target_node_label: str = "DatabricksWorkspace"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("workspace_node_id")},
    )
    source_node_label: str = "DatabricksAccountServicePrincipal"
    source_node_matcher: SourceNodeMatcher = make_source_node_matcher(
        {"id": PropertyRef("principal_id")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "ASSIGNED_TO"
    properties: DatabricksWorkspaceAssignmentRelProperties = (
        DatabricksWorkspaceAssignmentRelProperties()
    )

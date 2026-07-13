"""MatchLink schemas for materialized Scaleway IAM permission edges.

Scaleway IAM is coarse-grained: a Policy applies to a principal (user,
application or group) and holds Rules, each granting one or more named
permission sets scoped to a Project or the whole Organization. The API exposes
neither the individual actions inside a permission set nor per-resource ARNs, so
the AWS/GCP/Azure permission_relationships engine (which matches
action-string x resource-ARN) does not apply here.

Instead we materialize two factual, first-class edges from the policy/rule graph:

* ``(principal)-[:HAS_ROLE]->(:ScalewayPermissionSet)`` -- the canonical
  cross-provider role grant (mirrors AWS/GCP/Azure HAS_ROLE).
* ``(principal)-[:CAN_ACCESS]->(:ScalewayProject)`` -- the concrete scope of the
  grant, derived from ``rule.project_ids`` (organization-scoped rules fan out to
  every project). Resources hang off the project via ``RESOURCE``, so this makes
  principal -> resource access-path analysis traversable. ``has_condition`` flags
  grants that are only reachable under an IAM rule condition.
"""

from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.relationships import CartographyRelProperties
from cartography.models.core.relationships import CartographyRelSchema
from cartography.models.core.relationships import LinkDirection
from cartography.models.core.relationships import make_source_node_matcher
from cartography.models.core.relationships import make_target_node_matcher
from cartography.models.core.relationships import SourceNodeMatcher
from cartography.models.core.relationships import TargetNodeMatcher

# --- HAS_ROLE: principal -> permission set -------------------------------------


@dataclass(frozen=True)
class ScalewayHasRoleRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    _sub_resource_label: PropertyRef = PropertyRef(
        "_sub_resource_label", set_in_kwargs=True
    )
    _sub_resource_id: PropertyRef = PropertyRef("_sub_resource_id", set_in_kwargs=True)


@dataclass(frozen=True)
# (:ScalewayUser)-[:HAS_ROLE]->(:ScalewayPermissionSet)
class ScalewayUserToPermissionSetMatchLink(CartographyRelSchema):
    source_node_label: str = "ScalewayUser"
    source_node_matcher: SourceNodeMatcher = make_source_node_matcher(
        {"id": PropertyRef("user_id")},
    )
    target_node_label: str = "ScalewayPermissionSet"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"name": PropertyRef("permission_set_name")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "HAS_ROLE"
    properties: ScalewayHasRoleRelProperties = ScalewayHasRoleRelProperties()


@dataclass(frozen=True)
# (:ScalewayApplication)-[:HAS_ROLE]->(:ScalewayPermissionSet)
class ScalewayApplicationToPermissionSetMatchLink(CartographyRelSchema):
    source_node_label: str = "ScalewayApplication"
    source_node_matcher: SourceNodeMatcher = make_source_node_matcher(
        {"id": PropertyRef("application_id")},
    )
    target_node_label: str = "ScalewayPermissionSet"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"name": PropertyRef("permission_set_name")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "HAS_ROLE"
    properties: ScalewayHasRoleRelProperties = ScalewayHasRoleRelProperties()


@dataclass(frozen=True)
# (:ScalewayGroup)-[:HAS_ROLE]->(:ScalewayPermissionSet)
class ScalewayGroupToPermissionSetMatchLink(CartographyRelSchema):
    source_node_label: str = "ScalewayGroup"
    source_node_matcher: SourceNodeMatcher = make_source_node_matcher(
        {"id": PropertyRef("group_id")},
    )
    target_node_label: str = "ScalewayPermissionSet"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"name": PropertyRef("permission_set_name")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "HAS_ROLE"
    properties: ScalewayHasRoleRelProperties = ScalewayHasRoleRelProperties()


# --- CAN_ACCESS: principal -> project (scope) ----------------------------------


@dataclass(frozen=True)
class ScalewayCanAccessRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    _sub_resource_label: PropertyRef = PropertyRef(
        "_sub_resource_label", set_in_kwargs=True
    )
    _sub_resource_id: PropertyRef = PropertyRef("_sub_resource_id", set_in_kwargs=True)
    # True when every grant path to this project is gated by an IAM rule condition.
    has_condition: PropertyRef = PropertyRef("has_condition")


@dataclass(frozen=True)
# (:ScalewayUser)-[:CAN_ACCESS]->(:ScalewayProject)
class ScalewayUserToProjectMatchLink(CartographyRelSchema):
    source_node_label: str = "ScalewayUser"
    source_node_matcher: SourceNodeMatcher = make_source_node_matcher(
        {"id": PropertyRef("user_id")},
    )
    target_node_label: str = "ScalewayProject"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("project_id")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "CAN_ACCESS"
    properties: ScalewayCanAccessRelProperties = ScalewayCanAccessRelProperties()


@dataclass(frozen=True)
# (:ScalewayApplication)-[:CAN_ACCESS]->(:ScalewayProject)
class ScalewayApplicationToProjectMatchLink(CartographyRelSchema):
    source_node_label: str = "ScalewayApplication"
    source_node_matcher: SourceNodeMatcher = make_source_node_matcher(
        {"id": PropertyRef("application_id")},
    )
    target_node_label: str = "ScalewayProject"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("project_id")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "CAN_ACCESS"
    properties: ScalewayCanAccessRelProperties = ScalewayCanAccessRelProperties()


@dataclass(frozen=True)
# (:ScalewayGroup)-[:CAN_ACCESS]->(:ScalewayProject)
class ScalewayGroupToProjectMatchLink(CartographyRelSchema):
    source_node_label: str = "ScalewayGroup"
    source_node_matcher: SourceNodeMatcher = make_source_node_matcher(
        {"id": PropertyRef("group_id")},
    )
    target_node_label: str = "ScalewayProject"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("project_id")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "CAN_ACCESS"
    properties: ScalewayCanAccessRelProperties = ScalewayCanAccessRelProperties()

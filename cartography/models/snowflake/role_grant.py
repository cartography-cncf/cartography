"""Snowflake role assignment and role hierarchy edges.

``GET /api/v2/roles/{name}/grants-of`` answers both questions at once: it lists
every grantee a role has been granted to, tagged ``USER`` or ``ROLE``. The two
cases become different edges because the ontology constrains them differently:

- Granting a role to a user is ``HAS_ROLE``, mandated for
  ``UserAccount``/``ServiceAccount`` to ``PermissionRole``.
- Granting a role to another role is ``INCLUDES``, mandated for
  ``PermissionRole`` to ``PermissionRole``, with the *composite* role as the
  source. This matches Snowflake's semantics: ``GRANT ROLE child TO ROLE parent``
  makes the parent inherit the child's privileges, so the traversal that matters
  starts at the parent and descends.

Unlike the grant edges in ``grant.py``, these name concrete node labels instead of
the shared ``SnowflakePrincipal`` label. Both carry mandated ontology labels, and
the CI guard that enforces those labels resolves a shared extra label only to
itself, so routing these through ``SnowflakePrincipal`` would silently exempt them
from the check. The label pairs here are few enough to enumerate, so they are
enumerated.

Snowflake roles are deliberately *not* labelled ``UserGroup``: that would pull in
the ``MEMBER_OF`` constraint and conflict with ``INCLUDES``. A Snowflake role is a
privilege holder, not a membership container.

Note that Snowflake does not allow granting a database role directly to a user,
which is why there is no user-to-database-role edge here.
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


@dataclass(frozen=True)
class SnowflakeRoleAssignmentRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    _sub_resource_label: PropertyRef = PropertyRef(
        "_sub_resource_label", set_in_kwargs=True
    )
    _sub_resource_id: PropertyRef = PropertyRef("_sub_resource_id", set_in_kwargs=True)
    granted_by: PropertyRef = PropertyRef(
        "granted_by", description="Name of the role that created the grant."
    )
    created_on: PropertyRef = PropertyRef(
        "created_on", description="When the role was granted."
    )


@dataclass(frozen=True)
# (:SnowflakeUser)-[:HAS_ROLE]->(:SnowflakeRole)
class SnowflakeUserToRoleMatchLink(CartographyRelSchema):
    """A Snowflake user has been granted this role."""

    target_node_label: str = "SnowflakeRole"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("role_id")},
    )
    source_node_label: str = "SnowflakeUser"
    source_node_matcher: SourceNodeMatcher = make_source_node_matcher(
        {"id": PropertyRef("grantee_id")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "HAS_ROLE"
    properties: SnowflakeRoleAssignmentRelProperties = (
        SnowflakeRoleAssignmentRelProperties()
    )


@dataclass(frozen=True)
# (:SnowflakeServiceUser)-[:HAS_ROLE]->(:SnowflakeRole)
class SnowflakeServiceUserToRoleMatchLink(CartographyRelSchema):
    """A Snowflake service user has been granted this role."""

    target_node_label: str = "SnowflakeRole"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("role_id")},
    )
    source_node_label: str = "SnowflakeServiceUser"
    source_node_matcher: SourceNodeMatcher = make_source_node_matcher(
        {"id": PropertyRef("grantee_id")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "HAS_ROLE"
    properties: SnowflakeRoleAssignmentRelProperties = (
        SnowflakeRoleAssignmentRelProperties()
    )


@dataclass(frozen=True)
# (:SnowflakeRole)-[:INCLUDES]->(:SnowflakeRole)
class SnowflakeRoleToRoleMatchLink(CartographyRelSchema):
    """A Snowflake role inherits the privileges of the role granted to it."""

    target_node_label: str = "SnowflakeRole"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("role_id")},
    )
    source_node_label: str = "SnowflakeRole"
    source_node_matcher: SourceNodeMatcher = make_source_node_matcher(
        {"id": PropertyRef("grantee_id")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "INCLUDES"
    properties: SnowflakeRoleAssignmentRelProperties = (
        SnowflakeRoleAssignmentRelProperties()
    )


@dataclass(frozen=True)
# (:SnowflakeRole)-[:INCLUDES]->(:SnowflakeDatabaseRole)
class SnowflakeRoleToDatabaseRoleMatchLink(CartographyRelSchema):
    """A Snowflake role inherits the privileges of the database role granted to it."""

    target_node_label: str = "SnowflakeDatabaseRole"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("role_id")},
    )
    source_node_label: str = "SnowflakeRole"
    source_node_matcher: SourceNodeMatcher = make_source_node_matcher(
        {"id": PropertyRef("grantee_id")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "INCLUDES"
    properties: SnowflakeRoleAssignmentRelProperties = (
        SnowflakeRoleAssignmentRelProperties()
    )


@dataclass(frozen=True)
# (:SnowflakeDatabaseRole)-[:INCLUDES]->(:SnowflakeDatabaseRole)
class SnowflakeDatabaseRoleToDatabaseRoleMatchLink(CartographyRelSchema):
    """A Snowflake database role inherits the privileges of the database role granted to it."""

    target_node_label: str = "SnowflakeDatabaseRole"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("role_id")},
    )
    source_node_label: str = "SnowflakeDatabaseRole"
    source_node_matcher: SourceNodeMatcher = make_source_node_matcher(
        {"id": PropertyRef("grantee_id")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "INCLUDES"
    properties: SnowflakeRoleAssignmentRelProperties = (
        SnowflakeRoleAssignmentRelProperties()
    )

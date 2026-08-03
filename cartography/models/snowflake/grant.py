"""Snowflake grant edges.

Snowflake's RBAC model connects six kinds of grantee to nearly forty kinds of
grantable object. Enumerating that as one relationship per label pair would mean
hundreds of near-identical classes and as many cleanup jobs, so every grantee
carries the shared ``SnowflakePrincipal`` label and every grantable object carries
the shared ``SnowflakeSecurable`` label. That collapses the whole grant graph onto
the four MatchLinks below.

These are MatchLinks rather than relationships on a node schema because both ends
are loaded by earlier syncs and the edges come from a separate data source (the
grant endpoints, or ``ACCOUNT_USAGE`` when the collector lacks ``MANAGE GRANTS``),
and because the edges carry their own properties. MatchLink cleanup is scoped by
``_sub_resource_id`` to the account being synced, so one account's sync cannot
delete another's grant edges.

Using the shared labels here costs nothing in verification: ``HAS_PRIVILEGE`` is a
Snowflake-specific edge with no entry in
``ONTOLOGY_REL_CONSTRAINTS``, so the CI guard has nothing to check either way.
That is not true of the role edges in ``role_grant.py``, which name concrete
labels for exactly that reason.
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
class SnowflakeGrantRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    _sub_resource_label: PropertyRef = PropertyRef(
        "_sub_resource_label", set_in_kwargs=True
    )
    _sub_resource_id: PropertyRef = PropertyRef("_sub_resource_id", set_in_kwargs=True)
    privileges: PropertyRef = PropertyRef(
        "privileges",
        description="Privileges the grantee holds on the object, aggregated into one list.",
    )
    grant_option: PropertyRef = PropertyRef(
        "grant_option",
        description=(
            "Whether the grantee may grant these privileges onward, which makes the "
            "grant transitively expandable."
        ),
    )
    granted_by: PropertyRef = PropertyRef(
        "granted_by",
        description="Name of the role that created the grant.",
    )


@dataclass(frozen=True)
# (:SnowflakePrincipal)-[:HAS_PRIVILEGE {privileges}]->(:SnowflakeSecurable)
class SnowflakeGrantMatchLink(CartographyRelSchema):
    """A Snowflake grantee holds privileges on a grantable Snowflake object."""

    target_node_label: str = "SnowflakeSecurable"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("securable_id")},
    )
    source_node_label: str = "SnowflakePrincipal"
    source_node_matcher: SourceNodeMatcher = make_source_node_matcher(
        {"id": PropertyRef("principal_id")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "HAS_PRIVILEGE"
    properties: SnowflakeGrantRelProperties = SnowflakeGrantRelProperties()

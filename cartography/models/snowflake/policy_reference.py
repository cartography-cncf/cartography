"""Snowflake policy attachment edges.

A policy object is inert until it is attached to something. Attachments live in
``SNOWFLAKE.ACCOUNT_USAGE.POLICY_REFERENCES``, which returns every kind of policy
attachment in one row shape: the policy, the object it is attached to, and for a
masking policy the specific column. Because the object can be almost anything that
can hold a policy (a table, a view, a column's parent table, a user, the account
itself), the target end uses the shared ``SnowflakeSecurable`` label, exactly as
the grant edges do.

There is one edge class per policy *source* label rather than one shared source
label. That is deliberate: it keeps each edge's endpoints readable in the schema
docs and in the ontology constraint checks, and the four classes cost nothing at
load time because the rows are already grouped by policy kind when they are
transformed.

These are separate edges rather than properties on a node schema because both ends
are loaded by earlier syncs and the attachments come from a different statement.
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
class SnowflakePolicyAppliedToRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    _sub_resource_label: PropertyRef = PropertyRef(
        "_sub_resource_label", set_in_kwargs=True
    )
    _sub_resource_id: PropertyRef = PropertyRef("_sub_resource_id", set_in_kwargs=True)
    ref_entity_domain: PropertyRef = PropertyRef(
        "ref_entity_domain",
        description=(
            "The kind of object the policy is attached to, such as TABLE, VIEW, USER "
            "or ACCOUNT."
        ),
    )
    ref_column_name: PropertyRef = PropertyRef(
        "ref_column_name",
        description=(
            "The column the policy protects, for a masking or projection policy. Null "
            "when the policy applies to the whole object."
        ),
    )
    policy_status: PropertyRef = PropertyRef(
        "policy_status",
        description=(
            "Whether the attachment is active. An inactive attachment leaves the "
            "object unprotected despite the policy being set."
        ),
    )


@dataclass(frozen=True)
# (:SnowflakeDataPolicy)-[:APPLIED_TO]->(:SnowflakeSecurable)
class SnowflakeDataPolicyAppliedToMatchLink(CartographyRelSchema):
    """A Snowflake data governance policy is attached to this object, restricting reads of it."""

    target_node_label: str = "SnowflakeSecurable"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("securable_id")},
    )
    source_node_label: str = "SnowflakeDataPolicy"
    source_node_matcher: SourceNodeMatcher = make_source_node_matcher(
        {"id": PropertyRef("policy_id")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "APPLIED_TO"
    properties: SnowflakePolicyAppliedToRelProperties = (
        SnowflakePolicyAppliedToRelProperties()
    )


@dataclass(frozen=True)
# (:SnowflakePasswordPolicy)-[:APPLIED_TO]->(:SnowflakeSecurable)
class SnowflakePasswordPolicyAppliedToMatchLink(CartographyRelSchema):
    """A Snowflake password policy governs the passwords of this object's users."""

    target_node_label: str = "SnowflakeSecurable"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("securable_id")},
    )
    source_node_label: str = "SnowflakePasswordPolicy"
    source_node_matcher: SourceNodeMatcher = make_source_node_matcher(
        {"id": PropertyRef("policy_id")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "APPLIED_TO"
    properties: SnowflakePolicyAppliedToRelProperties = (
        SnowflakePolicyAppliedToRelProperties()
    )


@dataclass(frozen=True)
# (:SnowflakeSessionPolicy)-[:APPLIED_TO]->(:SnowflakeSecurable)
class SnowflakeSessionPolicyAppliedToMatchLink(CartographyRelSchema):
    """A Snowflake session policy governs the session timeouts of this object's users."""

    target_node_label: str = "SnowflakeSecurable"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("securable_id")},
    )
    source_node_label: str = "SnowflakeSessionPolicy"
    source_node_matcher: SourceNodeMatcher = make_source_node_matcher(
        {"id": PropertyRef("policy_id")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "APPLIED_TO"
    properties: SnowflakePolicyAppliedToRelProperties = (
        SnowflakePolicyAppliedToRelProperties()
    )


@dataclass(frozen=True)
# (:SnowflakeAuthenticationPolicy)-[:APPLIED_TO]->(:SnowflakeSecurable)
class SnowflakeAuthenticationPolicyAppliedToMatchLink(CartographyRelSchema):
    """A Snowflake authentication policy governs how this object's users may authenticate."""

    target_node_label: str = "SnowflakeSecurable"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("securable_id")},
    )
    source_node_label: str = "SnowflakeAuthenticationPolicy"
    source_node_matcher: SourceNodeMatcher = make_source_node_matcher(
        {"id": PropertyRef("policy_id")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "APPLIED_TO"
    properties: SnowflakePolicyAppliedToRelProperties = (
        SnowflakePolicyAppliedToRelProperties()
    )

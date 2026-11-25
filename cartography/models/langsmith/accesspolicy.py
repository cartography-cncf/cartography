from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.relationships import CartographyRelProperties
from cartography.models.core.relationships import CartographyRelSchema
from cartography.models.core.relationships import LinkDirection
from cartography.models.core.relationships import make_target_node_matcher
from cartography.models.core.relationships import OtherRelationships
from cartography.models.core.relationships import TargetNodeMatcher


@dataclass(frozen=True)
class LangSmithAccessPolicyNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id", description="Access policy UUID.")
    name: PropertyRef = PropertyRef(
        "name", extra_index=True, description="Access policy name."
    )
    description: PropertyRef = PropertyRef(
        "description", description="Human-readable description of the policy."
    )
    effect: PropertyRef = PropertyRef(
        "effect",
        description="Whether the policy allows or denies the matched resources.",
    )
    condition_summary: PropertyRef = PropertyRef(
        "condition_summary",
        description=(
            "Flattened, human-readable rendering of the policy's attribute-based condition "
            "groups, for example "
            "'(runs:read on project: resource_tag_key:env equals prod)'."
        ),
    )
    condition_tag_keys: PropertyRef = PropertyRef(
        "condition_tag_keys",
        description=(
            "Resource tag keys the policy's conditions match on. Match them against "
            "LangSmithResourceTag.key to find the tagged resources a policy can apply to."
        ),
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class LangSmithAccessPolicyToOrganizationRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:LangSmithOrganization)-[:RESOURCE]->(:LangSmithAccessPolicy)
class LangSmithAccessPolicyToOrganizationRel(CartographyRelSchema):
    """Links an organization to one of its access policies."""

    target_node_label: str = "LangSmithOrganization"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("ORG_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: LangSmithAccessPolicyToOrganizationRelProperties = (
        LangSmithAccessPolicyToOrganizationRelProperties()
    )


@dataclass(frozen=True)
class LangSmithAccessPolicyToRoleRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:LangSmithAccessPolicy)-[:ATTACHED_TO]->(:LangSmithRole)
class LangSmithAccessPolicyToRoleRel(CartographyRelSchema):
    """An access policy narrows the resources a role applies to."""

    target_node_label: str = "LangSmithRole"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("role_ids", one_to_many=True)},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "ATTACHED_TO"
    properties: LangSmithAccessPolicyToRoleRelProperties = (
        LangSmithAccessPolicyToRoleRelProperties()
    )


@dataclass(frozen=True)
class LangSmithAccessPolicySchema(CartographyNodeSchema):
    """
    An attribute-based access control policy. Policies attach to roles and user groups
    and restrict or extend which tagged resources their permissions apply to.
    """

    label: str = "LangSmithAccessPolicy"
    properties: LangSmithAccessPolicyNodeProperties = (
        LangSmithAccessPolicyNodeProperties()
    )
    sub_resource_relationship: LangSmithAccessPolicyToOrganizationRel = (
        LangSmithAccessPolicyToOrganizationRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            LangSmithAccessPolicyToRoleRel(),
        ],
    )

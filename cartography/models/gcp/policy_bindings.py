from dataclasses import dataclass
from dataclasses import field
from dataclasses import make_dataclass
from typing import ClassVar

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.relationships import CartographyRelProperties
from cartography.models.core.relationships import CartographyRelSchema
from cartography.models.core.relationships import LinkDirection
from cartography.models.core.relationships import make_source_node_matcher
from cartography.models.core.relationships import make_target_node_matcher
from cartography.models.core.relationships import MatchLinkSubResource
from cartography.models.core.relationships import OtherRelationships
from cartography.models.core.relationships import SourceNodeMatcher
from cartography.models.core.relationships import TargetNodeMatcher
from cartography.models.gcp.resource_catalog import GCP_POLICY_BINDING_TARGET_LABELS


@dataclass(frozen=True)
class GCPPolicyBindingNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "id",
        description=(
            "Binding identifier in `{resource}_{role}` form. Conditional bindings "
            "append `_{hash}`, where `hash` is the first eight hexadecimal "
            "characters of the SHA-256 condition-expression digest."
        ),
    )
    role: PropertyRef = PropertyRef(
        "role", description="The name of the GCP role being granted."
    )
    resource: PropertyRef = PropertyRef(
        "resource",
        description="The full resource name where the policy binding is attached.",
    )
    resource_type: PropertyRef = PropertyRef(
        "resource_type", description="The type of resource."
    )
    members: PropertyRef = PropertyRef(
        "members",
        description="A list of principal email addresses that are granted the role. The synthetic GCP principals `allUsers` and `allAuthenticatedUsers` are NOT included here; presence of either is reflected in `is_public` instead.",
    )
    wif_pools: PropertyRef = PropertyRef(
        "wif_pools",
        description="A list of Workload Identity Federation pool resource names (`projects/{N}/locations/global/workloadIdentityPools/{POOL}`) referenced by `principal://` or `principalSet://` members of this binding.",
    )
    # Domain-scoped grants (domain:{domain}). These don't resolve to a single
    # GCPPrincipal node, but are retained for visibility (e.g. broad-access audits).
    domains: PropertyRef = PropertyRef(
        "domains",
        description="A list of domains (`domain:{domain}`) granted the role. These do not resolve to a single `GCPPrincipal` node, but are retained for visibility (e.g. broad-access audits).",
    )
    is_public: PropertyRef = PropertyRef(
        "is_public",
        extra_index=True,
        description="True if the binding includes the `allUsers` or `allAuthenticatedUsers` principal. Combine with `has_condition = false` to reason about unconditional public exposure.",
    )
    has_condition: PropertyRef = PropertyRef(
        "has_condition",
        extra_index=True,
        description="A boolean indicating if the policy binding has a condition attached.",
    )
    condition_title: PropertyRef = PropertyRef(
        "condition_title", description="The title of the condition."
    )
    condition_expression: PropertyRef = PropertyRef(
        "condition_expression", description="The expression of the condition."
    )
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last time the node was updated.",
    )


@dataclass(frozen=True)
class GCPPolicyBindingResourceRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last sync that observed this data.",
    )


@dataclass(frozen=True)
class GCPPolicyBindingToProjectRel(CartographyRelSchema):
    target_node_label: str = "GCPProject"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("PROJECT_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: GCPPolicyBindingResourceRelProperties = (
        GCPPolicyBindingResourceRelProperties()
    )


@dataclass(frozen=True)
class GCPPolicyBindingToOrganizationRel(CartographyRelSchema):
    target_node_label: str = "GCPOrganization"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("ORG_RESOURCE_NAME", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: GCPPolicyBindingResourceRelProperties = (
        GCPPolicyBindingResourceRelProperties()
    )


@dataclass(frozen=True)
class GCPPolicyBindingToFolderRel(CartographyRelSchema):
    target_node_label: str = "GCPFolder"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("FOLDER_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: GCPPolicyBindingResourceRelProperties = (
        GCPPolicyBindingResourceRelProperties()
    )


@dataclass(frozen=True)
class GCPPolicyBindingToPrincipalRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last sync that observed this data.",
    )


@dataclass(frozen=True)
class GCPPolicyBindingToPrincipalRel(CartographyRelSchema):
    target_node_label: str = "GCPPrincipal"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"email": PropertyRef("members", one_to_many=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "HAS_ALLOW_POLICY"
    properties: GCPPolicyBindingToPrincipalRelProperties = (
        GCPPolicyBindingToPrincipalRelProperties()
    )


@dataclass(frozen=True)
class GCPPolicyBindingToWifPoolRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last sync that observed this data.",
    )


@dataclass(frozen=True)
class GCPPolicyBindingToWifPoolRel(CartographyRelSchema):
    target_node_label: str = "GCPWorkloadIdentityPool"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("wif_pools", one_to_many=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "HAS_ALLOW_POLICY"
    properties: GCPPolicyBindingToWifPoolRelProperties = (
        GCPPolicyBindingToWifPoolRelProperties()
    )


@dataclass(frozen=True)
class GCPPolicyBindingToRoleRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last sync that observed this data.",
    )


@dataclass(frozen=True)
class GCPPolicyBindingToRoleRel(CartographyRelSchema):
    target_node_label: str = "GCPRole"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"name": PropertyRef("role")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "GRANTS_ROLE"
    properties: GCPPolicyBindingToRoleRelProperties = (
        GCPPolicyBindingToRoleRelProperties()
    )


@dataclass(frozen=True)
class GCPPolicyBindingSchema(CartographyNodeSchema):
    """A Google Cloud IAM policy binding that grants a role on a resource."""

    label: str = "GCPPolicyBinding"
    properties: GCPPolicyBindingNodeProperties = GCPPolicyBindingNodeProperties()
    sub_resource_relationship: GCPPolicyBindingToProjectRel = (
        GCPPolicyBindingToProjectRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            GCPPolicyBindingToPrincipalRel(),
            GCPPolicyBindingToWifPoolRel(),
            GCPPolicyBindingToRoleRel(),
        ]
    )


@dataclass(frozen=True)
class GCPOrganizationPolicyBindingSchema(CartographyNodeSchema):
    """A Google Cloud IAM policy binding that grants a role on a resource."""

    label: str = "GCPPolicyBinding"
    properties: GCPPolicyBindingNodeProperties = GCPPolicyBindingNodeProperties()
    sub_resource_relationship: GCPPolicyBindingToOrganizationRel = (
        GCPPolicyBindingToOrganizationRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            GCPPolicyBindingToPrincipalRel(),
            GCPPolicyBindingToWifPoolRel(),
            GCPPolicyBindingToRoleRel(),
        ]
    )


@dataclass(frozen=True)
class GCPFolderPolicyBindingSchema(CartographyNodeSchema):
    """A Google Cloud IAM policy binding that grants a role on a resource."""

    label: str = "GCPPolicyBinding"
    properties: GCPPolicyBindingNodeProperties = GCPPolicyBindingNodeProperties()
    sub_resource_relationship: GCPPolicyBindingToFolderRel = (
        GCPPolicyBindingToFolderRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            GCPPolicyBindingToPrincipalRel(),
            GCPPolicyBindingToWifPoolRel(),
            GCPPolicyBindingToRoleRel(),
        ]
    )


@dataclass(frozen=True)
class GCPPolicyBindingAppliesToRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last sync that observed this data.",
    )
    _sub_resource_label: PropertyRef = PropertyRef(
        "_sub_resource_label",
        set_in_kwargs=True,
    )
    _sub_resource_id: PropertyRef = PropertyRef(
        "_sub_resource_id",
        set_in_kwargs=True,
    )


@dataclass(frozen=True)
class GCPPolicyBindingAppliesToMatchLink(CartographyRelSchema):
    """
    MatchLink schema that connects a GCPPolicyBinding to the concrete resource
    node it applies to.

    target_node_label is set dynamically at instantiation (e.g. "GCPProject",
    "GCPBucket") so a single binding can be matched unambiguously by (id, label)
    because raw resource_id alone is ambiguous across resource types.
    """

    __cartography_introspection_exclude__: ClassVar[bool] = True
    source_node_label: str = "GCPPolicyBinding"
    source_node_matcher: SourceNodeMatcher = make_source_node_matcher(
        {"id": PropertyRef("binding_id")},
    )
    target_node_label: str = "GCPResource"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("target_id")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "APPLIES_TO"
    properties: GCPPolicyBindingAppliesToRelProperties = (
        GCPPolicyBindingAppliesToRelProperties()
    )
    source_node_sub_resource: MatchLinkSubResource = MatchLinkSubResource(
        target_node_label="GCPProject",
        target_node_matcher=make_target_node_matcher(
            {"id": PropertyRef("_sub_resource_id", set_in_kwargs=True)},
        ),
        direction=LinkDirection.INWARD,
        rel_label="RESOURCE",
    )


def _make_policy_binding_applies_to_schema(
    target_label: str,
) -> type[GCPPolicyBindingAppliesToMatchLink]:
    class_name = f"GCPPolicyBindingAppliesTo{target_label.removeprefix('GCP')}MatchLink"
    schema_type = make_dataclass(
        class_name,
        [("target_node_label", str, field(default=target_label))],
        bases=(GCPPolicyBindingAppliesToMatchLink,),
        namespace={
            "__cartography_introspection_exclude__": False,
            "__doc__": (
                "Connects a GCP IAM policy binding to the concrete resource "
                "where the policy applies."
            ),
        },
        frozen=True,
    )
    schema_type.__module__ = __name__
    return schema_type


GCP_POLICY_BINDING_APPLIES_TO_SCHEMA_TYPES = {
    target_label: _make_policy_binding_applies_to_schema(target_label)
    for target_label in GCP_POLICY_BINDING_TARGET_LABELS
}
globals().update(
    {
        schema_type.__name__: schema_type
        for schema_type in GCP_POLICY_BINDING_APPLIES_TO_SCHEMA_TYPES.values()
    }
)

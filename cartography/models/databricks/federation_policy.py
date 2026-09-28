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
class DatabricksFederationPolicyNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "id",
        description="Account-scoped Databricks federation policy ID.",
    )
    name: PropertyRef = PropertyRef(
        "name",
        description="Federation policy name.",
    )
    uid: PropertyRef = PropertyRef(
        "uid",
        extra_index=True,
        description="Server-assigned federation policy UID.",
    )
    description: PropertyRef = PropertyRef(
        "description",
        description="Federation policy description.",
    )
    # Flattened out of the nested ``oidc_policy`` block; issuer + audiences are
    # the fields a security query needs to reason about who can federate in.
    issuer: PropertyRef = PropertyRef(
        "issuer",
        description="OIDC token issuer accepted by the policy.",
    )
    subject_claim: PropertyRef = PropertyRef(
        "subject_claim",
        description="OIDC claim used to identify the federated subject.",
    )
    audiences: PropertyRef = PropertyRef(
        "audiences",
        description="OIDC audiences accepted by the policy.",
    )
    # Set only for service-principal-scoped policies: the numeric SP id the
    # policy federates into. Absent (None) for account-wide policies. Kept as a
    # single node model with an optional field so both policy scopes share one
    # label and cleanup.
    service_principal_id: PropertyRef = PropertyRef(
        "service_principal_id",
        description="SCIM ID for a service-principal-scoped policy.",
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class DatabricksFederationPolicyToAccountRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:DatabricksAccount)-[:RESOURCE]->(:DatabricksFederationPolicy)
class DatabricksFederationPolicyToAccountRel(CartographyRelSchema):
    """A Databricks account owns an account-level resource."""

    target_node_label: str = "DatabricksAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("ACCOUNT_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: DatabricksFederationPolicyToAccountRelProperties = (
        DatabricksFederationPolicyToAccountRelProperties()
    )


@dataclass(frozen=True)
class DatabricksFederationPolicyToServicePrincipalRelProperties(
    CartographyRelProperties
):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:DatabricksFederationPolicy)-[:OWNED_BY]->(:DatabricksAccountServicePrincipal)
class DatabricksFederationPolicyToServicePrincipalRel(CartographyRelSchema):
    """A federation policy is owned by its account service principal."""

    target_node_label: str = "DatabricksAccountServicePrincipal"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        # Only service-principal-scoped policies carry ``sp_node_id``; account-wide
        # policies leave it None and this edge simply does not form for them.
        {"id": PropertyRef("sp_node_id")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "OWNED_BY"
    properties: DatabricksFederationPolicyToServicePrincipalRelProperties = (
        DatabricksFederationPolicyToServicePrincipalRelProperties()
    )


@dataclass(frozen=True)
class DatabricksFederationPolicySchema(CartographyNodeSchema):
    """A Databricks account or service principal federation policy."""

    label: str = "DatabricksFederationPolicy"
    properties: DatabricksFederationPolicyNodeProperties = (
        DatabricksFederationPolicyNodeProperties()
    )
    sub_resource_relationship: DatabricksFederationPolicyToAccountRel = (
        DatabricksFederationPolicyToAccountRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [DatabricksFederationPolicyToServicePrincipalRel()],
    )

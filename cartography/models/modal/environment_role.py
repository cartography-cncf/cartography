from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.nodes import ExtraNodeLabels
from cartography.models.core.relationships import CartographyRelProperties
from cartography.models.core.relationships import CartographyRelSchema
from cartography.models.core.relationships import LinkDirection
from cartography.models.core.relationships import make_source_node_matcher
from cartography.models.core.relationships import make_target_node_matcher
from cartography.models.core.relationships import SourceNodeMatcher
from cartography.models.core.relationships import TargetNodeMatcher
from cartography.models.ontology.labels import PERMISSION_ROLE


@dataclass(frozen=True)
class ModalEnvironmentRoleNodeProperties(CartographyNodeProperties):
    # Modal has no role object, so the id is synthesised as "<environment_id>/<role>".
    id: PropertyRef = PropertyRef(
        "id", description="Synthesised as `<environment_id>/<role>`."
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    # viewer, contributor or no-access (normalised from the ENVIRONMENT_ROLE_* enum).
    name: PropertyRef = PropertyRef(
        "name", extra_index=True, description="`viewer`, `contributor` or `no-access`."
    )
    scope: PropertyRef = PropertyRef("scope", description="Always `environment`.")


@dataclass(frozen=True)
class ModalEnvironmentRoleToEnvironmentRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:ModalEnvironment)-[:RESOURCE]->(:ModalEnvironmentRole)
class ModalEnvironmentRoleToEnvironmentRel(CartographyRelSchema):
    target_node_label: str = "ModalEnvironment"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("ENVIRONMENT_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: ModalEnvironmentRoleToEnvironmentRelProperties = (
        ModalEnvironmentRoleToEnvironmentRelProperties()
    )


@dataclass(frozen=True)
# Modal's per-environment RBAC roles are a fixed builtin set rather than API objects.
# Materialising them as PermissionRole nodes (rather than a property on the principal) is
# what lets Modal RBAC participate in the cross-provider HAS_ROLE rules, since
# ONTOLOGY_REL_CONSTRAINTS already blesses UserAccount/ServiceAccount -> PermissionRole.
class ModalEnvironmentRoleSchema(CartographyNodeSchema):
    """Represents one of Modal's builtin per-environment roles (`viewer`, `contributor`, `no-access`). Derived from the role enum; id is synthesised as `<environment_id>/<role>`."""

    label: str = "ModalEnvironmentRole"
    properties: ModalEnvironmentRoleNodeProperties = (
        ModalEnvironmentRoleNodeProperties()
    )
    sub_resource_relationship: ModalEnvironmentRoleToEnvironmentRel = (
        ModalEnvironmentRoleToEnvironmentRel()
    )
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels([PERMISSION_ROLE])


@dataclass(frozen=True)
class ModalPrincipalToEnvironmentRoleRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    _sub_resource_label: PropertyRef = PropertyRef(
        "_sub_resource_label", set_in_kwargs=True
    )
    _sub_resource_id: PropertyRef = PropertyRef("_sub_resource_id", set_in_kwargs=True)


@dataclass(frozen=True)
# (:ModalUser)-[:HAS_ROLE]->(:ModalEnvironmentRole)
# A MatchLink because the binding comes from EnvironmentGetRoles, a different RPC from the
# one that produced either endpoint, and both endpoints are already loaded by the time it
# runs.
class ModalUserToEnvironmentRoleMatchLink(CartographyRelSchema):
    source_node_label: str = "ModalUser"
    source_node_matcher: SourceNodeMatcher = make_source_node_matcher(
        {"id": PropertyRef("user_id")},
    )
    target_node_label: str = "ModalEnvironmentRole"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("role_id")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "HAS_ROLE"
    properties: ModalPrincipalToEnvironmentRoleRelProperties = (
        ModalPrincipalToEnvironmentRoleRelProperties()
    )


@dataclass(frozen=True)
# (:ModalServiceUser)-[:HAS_ROLE]->(:ModalEnvironmentRole)
class ModalServiceUserToEnvironmentRoleMatchLink(CartographyRelSchema):
    source_node_label: str = "ModalServiceUser"
    source_node_matcher: SourceNodeMatcher = make_source_node_matcher(
        {"id": PropertyRef("service_user_id")},
    )
    target_node_label: str = "ModalEnvironmentRole"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("role_id")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "HAS_ROLE"
    properties: ModalPrincipalToEnvironmentRoleRelProperties = (
        ModalPrincipalToEnvironmentRoleRelProperties()
    )

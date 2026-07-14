from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.nodes import ExtraNodeLabels
from cartography.models.core.relationships import CartographyRelProperties
from cartography.models.core.relationships import CartographyRelSchema
from cartography.models.core.relationships import LinkDirection
from cartography.models.core.relationships import make_target_node_matcher
from cartography.models.core.relationships import OtherRelationships
from cartography.models.core.relationships import TargetNodeMatcher


@dataclass(frozen=True)
class DOProjectNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id", description="DigitalOcean project UUID.")
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last update.",
    )
    account_id: PropertyRef = PropertyRef(
        "ACCOUNT_ID",
        set_in_kwargs=True,
        description="ID of the account that owns the project.",
    )
    name: PropertyRef = PropertyRef("name", description="Project name.")
    owner_uuid: PropertyRef = PropertyRef(
        "owner_uuid",
        description="UUID of the project owner.",
    )
    description: PropertyRef = PropertyRef(
        "description",
        description="Project description.",
    )
    environment: PropertyRef = PropertyRef(
        "environment",
        description="Environment classification of project resources.",
    )
    is_default: PropertyRef = PropertyRef(
        "is_default",
        description="Whether unspecified resources default to this project.",
    )
    created_at: PropertyRef = PropertyRef(
        "created_at",
        description="Project creation timestamp.",
    )
    updated_at: PropertyRef = PropertyRef(
        "updated_at",
        description="Project update timestamp.",
    )


@dataclass(frozen=True)
class DOProjectToAccountRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:DOAccount)-[:RESOURCE]->(:DOProject)
class DOProjectToAccountRel(CartographyRelSchema):
    """The account contains the project."""

    target_node_label: str = "DOAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("ACCOUNT_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: DOProjectToAccountRelProperties = DOProjectToAccountRelProperties()


@dataclass(frozen=True)
# (:DOAccount)<-[:RESOURCE]-(:DOProject) - Backwards compatibility
class DOProjectToAccountDeprecatedRel(CartographyRelSchema):
    """Deprecated compatibility edge linking a project to its account."""

    target_node_label: str = "DOAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("ACCOUNT_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "RESOURCE"
    properties: DOProjectToAccountRelProperties = DOProjectToAccountRelProperties()


@dataclass(frozen=True)
class DOProjectSchema(CartographyNodeSchema):
    """A project in a DigitalOcean account."""

    label: str = "DOProject"
    properties: DOProjectNodeProperties = DOProjectNodeProperties()
    sub_resource_relationship: DOProjectToAccountRel = DOProjectToAccountRel()
    # DEPRECATED: for backward compatibility, will be removed in v1.0.0
    other_relationships: OtherRelationships = OtherRelationships(
        rels=[DOProjectToAccountDeprecatedRel()],
    )
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(["Tenant"])

from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.nodes import ExtraNodeLabels
from cartography.models.core.relationships import CartographyRelProperties
from cartography.models.core.relationships import CartographyRelSchema
from cartography.models.core.relationships import LinkDirection
from cartography.models.core.relationships import make_target_node_matcher
from cartography.models.core.relationships import TargetNodeMatcher


@dataclass(frozen=True)
class SalesforcePermissionSetNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("Id")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    name: PropertyRef = PropertyRef("Name", extra_index=True)
    label: PropertyRef = PropertyRef("Label")
    type: PropertyRef = PropertyRef("Type")
    is_owned_by_profile: PropertyRef = PropertyRef("IsOwnedByProfile")


@dataclass(frozen=True)
class SalesforcePermissionSetToOrganizationRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:SalesforceOrganization)-[:RESOURCE]->(:SalesforcePermissionSet)
class SalesforcePermissionSetToOrganizationRel(CartographyRelSchema):
    target_node_label: str = "SalesforceOrganization"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("ORG_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: SalesforcePermissionSetToOrganizationRelProperties = (
        SalesforcePermissionSetToOrganizationRelProperties()
    )


@dataclass(frozen=True)
class SalesforcePermissionSetSchema(CartographyNodeSchema):
    label: str = "SalesforcePermissionSet"
    properties: SalesforcePermissionSetNodeProperties = (
        SalesforcePermissionSetNodeProperties()
    )
    sub_resource_relationship: SalesforcePermissionSetToOrganizationRel = (
        SalesforcePermissionSetToOrganizationRel()
    )
    # A permission set is an additive bundle of permissions -> PermissionRole ontology.
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(["PermissionRole"])

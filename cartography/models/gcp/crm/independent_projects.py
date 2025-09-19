from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema


@dataclass(frozen=True)
class GCPIndependentProjectNodeProperties(CartographyNodeProperties):
    """Properties for GCP Projects that have no parent (org or folder)"""

    id: PropertyRef = PropertyRef("projectId")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    projectid: PropertyRef = PropertyRef("projectId", extra_index=True)
    projectnumber: PropertyRef = PropertyRef("projectNumber")
    displayname: PropertyRef = PropertyRef("name")
    lifecyclestate: PropertyRef = PropertyRef("lifecycleState")
    is_orgless: PropertyRef = PropertyRef("is_orgless", set_in_kwargs=True)
    # No parent_org or parent_folder fields since these projects have no parent


@dataclass(frozen=True)
class GCPIndependentProjectSchema(CartographyNodeSchema):
    """Schema for GCP Projects without any parent organization or folder"""

    label: str = "GCPProject"  # Same label as regular projects
    properties: GCPIndependentProjectNodeProperties = (
        GCPIndependentProjectNodeProperties()
    )
    # No sub_resource_relationship since there's no parent
    # No other_relationships since there are no parent relationships
    # Set scoped_cleanup=False to generate unscoped cleanup queries for orgless projects
    scoped_cleanup: bool = False
    # Cascade delete all sub-resources when this node is deleted
    # This will delete all nodes that define this project as their sub_resource_relationship
    cascade_delete_sub_resources: bool = True

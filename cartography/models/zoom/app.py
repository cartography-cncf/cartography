from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.zoom.resource import ZoomAccountResourceRel


@dataclass(frozen=True)
class ZoomAppProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    account_id: PropertyRef = PropertyRef(
        "ACCOUNT_ID", set_in_kwargs=True, extra_index=True
    )
    app_id: PropertyRef = PropertyRef(
        "app_id", description="Marketplace app_id.", extra_index=False
    )
    name: PropertyRef = PropertyRef(
        "name", description="Marketplace app_name.", extra_index=True
    )
    installed: PropertyRef = PropertyRef(
        "installed",
        description="Present in the account_added list; does not enumerate individual user installations.",
        extra_index=True,
    )
    approved: PropertyRef = PropertyRef(
        "approved", description="Present in the approved_apps list.", extra_index=True
    )
    approval_type: PropertyRef = PropertyRef(
        "approval_type",
        description="approval_info.approved_type, such as forAllUser or forSpecificUser.",
        extra_index=False,
    )
    approval_required: PropertyRef = PropertyRef(
        "approval_required",
        description="Inverse of approval_info.app_approval_closed, when provided.",
        extra_index=False,
    )
    app_status: PropertyRef = PropertyRef(
        "app_status",
        description="Detail app_status is publication status, not installation state.",
        extra_index=False,
    )
    app_type: PropertyRef = PropertyRef(
        "app_type", description="Detail app_type.", extra_index=False
    )
    app_scopes: PropertyRef = PropertyRef(
        "app_scopes",
        description="Exact OAuth scope identifiers from app_scopes; empty when none are returned.",
        extra_index=False,
    )


@dataclass(frozen=True)
class ZoomAppSchema(CartographyNodeSchema):
    """An account-added or approved Marketplace app. Approval and installation are independent states."""

    label: str = "ZoomApp"
    properties: ZoomAppProperties = ZoomAppProperties()
    sub_resource_relationship: ZoomAccountResourceRel = ZoomAccountResourceRel()

from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.relationships import CartographyRelProperties
from cartography.models.core.relationships import CartographyRelSchema
from cartography.models.core.relationships import LinkDirection
from cartography.models.core.relationships import make_target_node_matcher
from cartography.models.core.relationships import TargetNodeMatcher


@dataclass(frozen=True)
class OktaLogStreamNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "id", description="Unique Okta log stream identifier."
    )
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last sync that observed this resource.",
    )
    name: PropertyRef = PropertyRef("name", description="Log stream name.")
    type: PropertyRef = PropertyRef(
        "type",
        description=(
            "Destination type, such as `aws_eventbridge` or "
            "`splunk_cloud_logstreaming`."
        ),
    )
    status: PropertyRef = PropertyRef(
        "status",
        description="Log stream status, `ACTIVE` or `INACTIVE`. Only active streams deliver System Log events.",
    )
    created: PropertyRef = PropertyRef(
        "created", description="Time when the log stream was created."
    )
    okta_last_updated: PropertyRef = PropertyRef(
        "okta_last_updated",
        description="Time when Okta last updated the log stream.",
    )
    aws_account_id: PropertyRef = PropertyRef(
        "aws_account_id",
        description="`aws_eventbridge` streams only. AWS account that receives the events.",
    )
    aws_region: PropertyRef = PropertyRef(
        "aws_region",
        description="`aws_eventbridge` streams only. AWS region of the EventBridge event source.",
    )
    aws_event_source_name: PropertyRef = PropertyRef(
        "aws_event_source_name",
        description="`aws_eventbridge` streams only. Name of the EventBridge partner event source.",
    )
    splunk_host: PropertyRef = PropertyRef(
        "splunk_host",
        description="`splunk_cloud_logstreaming` streams only. Splunk Cloud host that receives the events.",
    )
    splunk_edition: PropertyRef = PropertyRef(
        "splunk_edition",
        description="`splunk_cloud_logstreaming` streams only. Splunk Cloud edition, such as `aws` or `gcp`.",
    )


@dataclass(frozen=True)
class OktaLogStreamToOrganizationRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last sync that observed this relationship.",
    )


@dataclass(frozen=True)
class OktaLogStreamToOrganizationRel(CartographyRelSchema):
    """An Okta organization streams its System Log through a log stream."""

    target_node_label: str = "OktaOrganization"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("OKTA_ORG_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: OktaLogStreamToOrganizationRelProperties = (
        OktaLogStreamToOrganizationRelProperties()
    )


@dataclass(frozen=True)
class OktaLogStreamSchema(CartographyNodeSchema):
    """
    An Okta log stream that forwards System Log events to an external
    destination such as AWS EventBridge or Splunk Cloud. Requires the
    `okta.logStreams.read` scope.
    """

    label: str = "OktaLogStream"
    properties: OktaLogStreamNodeProperties = OktaLogStreamNodeProperties()
    sub_resource_relationship: OktaLogStreamToOrganizationRel = (
        OktaLogStreamToOrganizationRel()
    )

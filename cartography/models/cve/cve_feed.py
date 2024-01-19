from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema


@dataclass(frozen=True)
class CVEFeedNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef('FEED_ID')
    lastupdated: PropertyRef = PropertyRef('lastupdated', set_in_kwargs=True)
    format: PropertyRef = PropertyRef('format')
    version: PropertyRef = PropertyRef('version')
    timestamp: PropertyRef = PropertyRef('timestamp')


@dataclass(frozen=True)
class CVEFeedSchema(CartographyNodeSchema):
    label: str = 'CVEFeed'
    properties: CVEFeedNodeProperties = CVEFeedNodeProperties()

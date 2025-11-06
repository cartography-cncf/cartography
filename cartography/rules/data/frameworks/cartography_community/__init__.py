# Cartography Community Framework
from cartography.rules.data.frameworks.cartography_community.requirements.access_control import (
    cc_001,
)
from cartography.rules.spec.model import Framework

cartography_community_framework = Framework(
    id="CARTOGRAPHY_COMMUNITY",
    name="Cartography Community",
    description="Comprehensive security assessment framework based on community-driven best practices",
    version="1.0",
    requirements=(cc_001,),  # Access Control
    source_url="https://cartography.dev",
)

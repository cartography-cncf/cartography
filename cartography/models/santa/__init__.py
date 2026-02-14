# Santa data models

from cartography.models.santa.application import SantaObservedApplicationSchema
from cartography.models.santa.application_version import (
    SantaObservedApplicationVersionSchema,
)
from cartography.models.santa.machine import SantaMachineSchema
from cartography.models.santa.user import SantaUserSchema

__all__ = [
    "SantaMachineSchema",
    "SantaUserSchema",
    "SantaObservedApplicationSchema",
    "SantaObservedApplicationVersionSchema",
]

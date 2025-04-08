# cartography/models/msft365/__init__.py

from .userSchema import Msft365UserSchema, Msft365UserToGroupRelSchema
from .groupSchema import Msft365GroupSchema
from .deviceSchema import Msft365DeviceSchema, Msft365DeviceOwnerRelSchema, Msft365UserToDeviceRelSchema
from .ouSchema import (
    Msft365OrganizationalUnitSchema,
    Msft365OUToUserRelSchema,
    Msft365OUToGroupRelSchema,
    Msft365UserToOrgUnitRelSchema,
)

# cartography/models/msft365/__init__.py

from .userSchema import Msft365UserSchema, Msft365UserToGroupRelSchema
from .groupSchema import Msft365GroupSchema
from .deviceSchema import Msft365DeviceSchema, Msft365DeviceOwnerRelSchema
from .ouSchema import Msft365OrganizationalUnitSchema, Msft365OUToUserRelSchema, Msft365OUToGroupRelSchema

__all__ = [
    'Msft365UserSchema',
    'Msft365GroupSchema',
    'Msft365DeviceSchema',
    'Msft365OrganizationalUnitSchema',
    'Msft365UserToGroupRelSchema',
    'Msft365DeviceOwnerRelSchema',
    'Msft365OUToUserRelSchema',
    'Msft365OUToGroupRelSchema',
]

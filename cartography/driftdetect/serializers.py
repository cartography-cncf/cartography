from marshmallow import fields
from marshmallow import post_load
from marshmallow import Schema

from cartography.driftdetect.model import State
from cartography.driftdetect.shortcut import Shortcut


class StateSchema(Schema):
    """
    Schema to serialize and deserialize DriftStates from JSON.
    """

    name = fields.Str()
    validation_query = fields.Str()
    properties = fields.List(fields.Str())
    results = fields.List(fields.List(fields.Str()))

    @post_load
    def make_state(self, data, **kwargs):
        return State(
            data["name"],
            data["validation_query"],
            data["properties"],
            data["results"],
        )


class ShortcutSchema(Schema):
    """
    Schema to serialize and deserialize Shortcuts from JSON.
    """

    name = fields.Str()
    shortcuts = fields.Dict(keys=fields.Str(), values=fields.Str())

    @post_load
    def make_misc(self, data, **kwargs):
        return Shortcut(
            data["name"],
            data["shortcuts"],
        )

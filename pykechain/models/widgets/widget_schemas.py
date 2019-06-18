from pykechain.enums import WidgetTypes

widget_meta_schema = {
    "$schema": "http://json-schema.org/draft-06/schema#",
    "title": "Toplevel Widget Meta schema",
    "type": "object",
    "additionalProperties": True,
    "properties": {}
}

def get_widget_meta_schema(widget_type=WidgetTypes.UNDEFINED):
    return widget_meta_schema

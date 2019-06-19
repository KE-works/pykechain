from copy import deepcopy

from pykechain.enums import WidgetTypes

widget_meta_schema = {
    "$schema": "https://json-schema.org/schema#",
    "title": "Toplevel Widget Meta schema",
    "type": "object",
    "additionalProperties": True,
    "properties": {},
    "definitions": {
        "uuidString": {"type": "string",
                       "pattern": "^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$"},
        "nullString": {"type": ["string", "null"]},
        "positiveInteger": {"type": "integer", "minimum": 0},
        "booleanNull": {"type": ["boolean", "null"]}
    }
}


def get_widget_meta_schema(widget_type=WidgetTypes.UNDEFINED):
    return widget_meta_schema


# attachmentviewer_meta_schema = widget_meta_schema.update({
#     "properties": {
#         "propertyInstanceId": {"$ref": "#/definitions/uuidString"},
#         "customHeight": {"$ref": "#/defintions/nullPositiveInteger"},
#         "activityId": {"$ref": "#/definitions/uuidString"},
#         "showTitleValue": {"type": ["string", "null"], "enum": ["Custom Value", "Default"]},
#         "customTitle": {"$ref": "#/definitions/nullString"},
#     }
# })

attachmentviewer_meta_schema = deepcopy(widget_meta_schema)
attachmentviewer_meta_schema.update({
    "properties": {
        "propertyInstanceId": {"$ref": "#/definitions/uuidString"},
        "activityId": {"$ref": "#/definitions/uuidString"},
        "showTitleValue": {"$ref": "#/definitions/nullString"},
        "customTitle": {"$ref": "#/definitions/nullString"},
        "noPadding": {"$ref": "#/definitions/nullString"},
        "customHeight": {"$ref": "#/definitions/positiveInteger"},
        "alignment": {"$ref":"#/definitions/booleanNull"}
    },
    # "additionalProperties": True,
    "required": ["propertyInstanceId", "activityId"]
})

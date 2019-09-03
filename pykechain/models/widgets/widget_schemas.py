from copy import deepcopy

widget_meta_schema = {
    "$schema": "http://json-schema.org/draft-06/schema#",
    "title": "Toplevel Widget Meta schema",
    "type": "object",
    "additionalProperties": False,
    "properties": {},
    "definitions": {
        "uuidString": {"type": "string",
                       "pattern": "^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$"},
        "nullUuidString": {"type": ["string", "null"],
                           "pattern": "^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$"},
        "nullString": {"type": ["string", "null"]},
        "positiveInteger": {"type": ["integer", "null", "string"], "minimum": 0},
        "booleanNull": {"type": ["boolean", "null"]}
    }
}

undefined_meta_schema = deepcopy(widget_meta_schema)
undefined_meta_schema.update({"additionalProperties": True})

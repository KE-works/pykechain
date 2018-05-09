from pykechain.enums import PropertyVTypes

effects_jsonschema_stub = {
    "type": "object",
    "additionalProperties": False,
    "required": ["effect", "config"],
    "properties": {
        "effect": {"type": ["string", "null"]},
        "config": {"type": "object"}
    }
}

validator_jsonschema_stub = {
    "$schema": "http://json-schema.org/draft-04/schema#",
    "type": "object",
    "title": "Single Validator JSON schema",
    "additionalProperties": False,
    "required": ["vtype", "config"],
    "properties": {
        "vtype": {"type": "string", "enum": PropertyVTypes.values()},
        "config": {
            "type": "object",
            "properties": {
                "on_valid": {"type": "array", "items": effects_jsonschema_stub},
                "on_invalid": {"type": "array", "items": effects_jsonschema_stub}
            }
        }
    }
}

validators_options_json_schema = {
    "$schema": "http://json-schema.org/draft-04/schema#",
    "title": "Validators JSON schema",
    "type": "array",
    "items": validator_jsonschema_stub
}

options_json_schema = {
    "$schema": "http://json-schema.org/draft-04/schema#",
    "title": "Toplevel Property Options JSON schema",
    "type": "object",
    "additionalProperties": True,
    "properties": {
        # Validators
        "validators": validators_options_json_schema,

        # Single Select Lists
        "value_choices": {"type": "array"}
    }
}

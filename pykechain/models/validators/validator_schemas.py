import copy

from pykechain.enums import PropertyType, PropertyVTypes, _AllRepresentations
#
# Validators and Validator Effects
#
from pykechain.utils import UUID_REGEX_PATTERN

effects_jsonschema_stub = {
    "type": "object",
    "additionalProperties": False,
    "required": ["effect", "config"],
    "properties": {
        "effect": {"type": ["string", "null"]},
        "config": {"type": "object"},
    },
}

validator_jsonschema_stub = {
    "$schema": "http://json-schema.org/draft-07/schema#",
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
                "on_invalid": {"type": "array", "items": effects_jsonschema_stub},
            },
        },
    },
}

validators_options_json_schema = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "title": "Validators JSON schema",
    "type": "array",
    "items": validator_jsonschema_stub,
}

fileextensionvalidator_schema = copy.deepcopy(validator_jsonschema_stub)
fileextensionvalidator_schema["properties"]["config"]["properties"].update(
    {"accept": {"type": "array", "items": {"type": ["string", "null"]}}}
)

filesizevalidator_schema = copy.deepcopy(validator_jsonschema_stub)
filesizevalidator_schema["properties"]["config"]["properties"].update(
    {"maxSize": {"type": "number", "minimum": 0, "multipleOf": 1.0}}
)

#
# Representation of a property configurations
#

representation_jsonschema_stub = {
    "type": "object",
    "additionalProperties": False,
    "required": ["rtype", "config"],
    "properties": {
        "rtype": {"type": "string", "enum": _AllRepresentations.values()},
        "config": {"type": "object"},
    },
}

representation_options_json_schema = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "title": "Validators JSON schema",
    "type": "array",
    "items": representation_jsonschema_stub,
}

#
# Property Value Options json schema
#

options_json_schema = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "title": "Toplevel Property Options JSON schema",
    "type": "object",
    "additionalProperties": True,
    "properties": {
        # Validators
        "validators": validators_options_json_schema,
        # Reference Property additional options to hide columns and store filters
        "propmodels_excl": {"type": "array"},
        "propmodels_incl": {"type": "array"},
        "prefilters": {"type": "object"},
        # Representations
        "representation": representation_options_json_schema,
    },
}


#
# Scope Project Info json schema
#
# this is integregal copy of the definition in the KE-chain backend.
project_info_property_types = [
    PropertyType.CHAR_VALUE,
    PropertyType.TEXT_VALUE,
    PropertyType.INT_VALUE,
    PropertyType.FLOAT_VALUE,
    PropertyType.LINK_VALUE,
    PropertyType.DATETIME_VALUE,
    PropertyType.DATE_VALUE,
    PropertyType.TIME_VALUE,
    PropertyType.DURATION_VALUE,
]

scope_project_info_jsonschema = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "title": "Toplevel Scope Project info JSON schema",
    "description": "The project information properties that are part of the scope",
    "type": "array",
    "items": {
        "type": "object",
        "additionalProperties": False,
        "required": ["id", "name", "property_type", "value"],
        "properties": {
            "id": {"type": "integer", "minimum": 0},
            "name": {
                "type": ["string", "null"],
            },
            "property_type": {
                "type": "string",
                "enum": project_info_property_types,
                "default": PropertyType.CHAR_VALUE,
            },
            "value": {},
            "unit": {
                "type": ["string", "null"],
            },
            "description": {
                "type": ["string", "null"],
            },
        },
    },
}

#
# Prefill parts Info json schema
#
# this is integregal copy of the definition in the KE-chain backend.
prefill_property_stub = {
    "type": "object",
    "additionalProperties": False,
    "required": ["property_id", "value"],
    "properties": {
        "property_id": {"$ref": "#/definitions/uuidString"},
        "value": {},
    },
}
prefill_part_stub = {
    "type": "object",
    "additionalProperties": False,
    "required": ["name", "part_properties"],
    "properties": {
        "name": {"type": "string"},
        "part_properties": {"type": "array", "items": prefill_property_stub},
    },
}
form_collection_prefill_parts_schema = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "title": "FormCollection Prefill Parts schema",
    "version": "1.0.0",
    "type": "object",
    "additionalProperties": True,
    # propertyNames is a schema that all of an object's properties must be valid against
    # ref: https://json-schema.org/understanding-json-schema/reference/object.html#property-names
    "propertyNames": {"pattern": UUID_REGEX_PATTERN},
    # patternProperties is a schema that all of an objects property (named) must be valid against
    # ref: https://json-schema.org/understanding-json-schema/reference/object.html#pattern-properties
    "patternProperties": {
        UUID_REGEX_PATTERN: {
            "type": "array",
            "items": prefill_part_stub,
        }
    },
    "definitions": {
        "uuidString": {
            "type": "string",
            "pattern": UUID_REGEX_PATTERN,
        },
        "nullUuidString": {
            "type": ["string", "null"],
            "pattern": UUID_REGEX_PATTERN,
        },
        "nullString": {"type": ["string", "null"]},
        "positiveInteger": {"type": ["integer", "null"], "minimum": 0},
        "booleanNull": {"type": ["boolean", "null"]},
    },
}

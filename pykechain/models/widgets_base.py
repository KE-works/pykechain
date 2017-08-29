from pykechain.enums import ComponentXType

uuid_pattern = "^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$"
uuid_string = {"type": "string", "pattern": uuid_pattern}
component_json_schema = {
    "$schema": "http://json-schema.org/draft-04/schema#",
    "title": "Component JSON Schema",
    "type": "object",
    "properties": {
        "xtype": {
            "type": "string",
            "enum": [ComponentXType.PROPERTYGRID, ComponentXType.SUPERGRID,
                     ComponentXType.FILTEREDGRID, ComponentXType.PAGINATEDSUPERGRID,
                     ComponentXType.PANEL, ComponentXType.TOOLBAR]
        },
        "filter": {
            "type": "object",
            "properties": {
                "part": uuid_string,
                "model": uuid_string,
                "parent": uuid_string
            }
        },
        "title": {"type": ["string", "null"]},
        "viewModel": {"type": "object"},
        # "model": {"type": "string"},
        # "parent": uuid_string
    },
    "required": ["xtype"]
}
widgetconfig_json_schema = {
    "$schema": "http://json-schema.org/draft-04/schema#",
    "title": "WidgetConfig JSON",
    "type": "object",
    "properties": {
        "components": {
            "type": "array",
            "items": component_json_schema
        }
    }
}


class WidgetComponent(object):
    """Widget Base Component for a customized widgets."""

    def __init__(self, json=None, **kwargs):
        """
        Customisation Component.

        :param json:
        :param kwargs:
        """
        if not json:
            self._json_data = dict(xtype="panel", **kwargs)
        else:
            assert 'xtype' in json, "A component of the Inspector customization needs an 'xtype', got {}".format(json)
            self._json_data = json

        self.xtype = self._json_data.get('xtype')
        self.title = self._json_data.get('title', None)
        self.validate()

    def validate(self):
        """Validate the component against the component JSON Schema.

        :return: None if valid
        :return: ValidationError
        """
        from jsonschema import validate
        return validate(self._json_data, component_json_schema)

    def as_dict(self):
        """Return the component as a dictionary."""
        return self._json_data

    def as_json(self):
        """Return the component as a rendered and valid JSON string."""
        return self.render()

    def render(self):
        """Return the component as a rendered and valid JSON string."""
        return json.dumps(self.as_dict(), indent=2)

    def __repr__(self):  # pragma: no cover
        return "<{} ({}) at {:#x}>".format(self.__class__.__name__, self.xtype, id(self))

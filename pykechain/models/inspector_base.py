import json

from jsonschema import ValidationError

from pykechain.enums import ComponentXType
from pykechain.exceptions import InspectorComponentError

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


class InspectorComponent(object):
    """Inspector Base Component for a customization."""

    def __init__(self, json=None, **kwargs):
        """
        Customisation Component.

        :param json:
        :param kwargs:
        """
        if not json:
            self._json_data = dict(xtype="panel", **kwargs)
        else:
            if 'xtype' not in json:
                raise ValidationError("A component of the Inspector customization needs an 'xtype', got {}".
                                      format(json))
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


class Customization(InspectorComponent):
    """Customization wrapper object."""

    def __init__(self, json=None, **kwargs):
        """Make a new Customization object that wraps the various components.

        :param json: (optional) provide a Customization json, will be validated
        :ivar components: list of components
        :raises ValueError, InspectorComponentError
        """
        self.components = []
        if json:
            if not isinstance(json, dict):
                raise ValueError("json needs to be deserialised as a dictionary first, use `json.loads()`")
            if 'components' not in json:
                raise InspectorComponentError("Customization need a 'components' key in the json, got {}".format(json))
            if not isinstance(json.get('components'), (list, tuple)):
                raise InspectorComponentError("Customization need a list of 'components', got {}".
                                              format(type(json.get('components'))))
            for component_json in json.get('components'):
                self.components.append(InspectorComponent(json=component_json))
            self.validate()

    def add_component(self, component):
        """Add a component to the internal components list."""
        if not isinstance(component, InspectorComponent):
            raise InspectorComponentError("Component need to be of instance InspectorComponent or an object based on "
                                          "InspectorComponent, got {}".format(type(component)))
        self.components.append(component)

    def validate(self):
        """Validate the Customization objects (including the internal components).

        :return: None if valid
        :raises: ValidationError
        """
        from jsonschema import validate
        return validate(self.as_dict(), widgetconfig_json_schema)

    def as_dict(self):
        """Return the Customization as dictionary."""
        return dict(components=[component.as_dict() for component in self.components])

    def as_json(self):
        """Return the Customization as rendered and valid JSON string."""
        return json.dumps(self.as_dict())

    def __repr__(self):  # pragma: no cover
        return "<{} ({} comp's) at {:#x}>".format(self.__class__.__name__, len(self.components), id(self))

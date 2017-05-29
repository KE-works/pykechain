import json

from pykechain.models import Base

uuid_pattern = "^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$"
uuid_string = {"type":"string", "pattern": uuid_pattern}
component_json_schema = {
    "$schema": "http://json-schema.org/draft-04/schema#",
    "title": "Component JSON Schema",
    "type": "object",
    "properties": {
        "xtype": {
            "type": "string",
            "enum": ["propertyGrid", "superGrid", "panel", "iframe", "filteredGrid", "paginatedSuperGrid"]
        },
        "filter": {
            "type": "object",
            "properties": {
                "part": uuid_string,
                "model": uuid_string,
                "parent": uuid_string
            }
        },
        "title": {"type": "string"},
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
    def __init__(self, json, **kwargs):
        if not json:
            self._json_data = dict(xtype="panel", **kwargs)
        else:
            assert 'xtype' in json, "A component of the Inspector customization needs an 'xtype', got {}".format(json)
            self._json_data = json

        self.xtype = self._json_data.get('xtype')
        self.title = self._json_data.get('title', None)
        self.validate()

    def validate(self):
        from jsonschema import validate
        return validate(self._json_data, component_json_schema)

    def as_dict(self):
        return self._json_data

    def as_json(self):
        return self.render()

    def render(self):
        return json.dumps(self._json_data, indent=2)

    def __repr__(self):
        return "<{} ({}) at {:#x}>".format(self.__class__.__name__, self.xtype, id(self))


class SuperGrid(InspectorComponent):
    def __init__(self, json=None, parent=None, model=None, **kwargs):
        if not json:
            super(self.__class__, self).__init__(json=dict(
                xtype="superGrid",
                parent=parent,
                model=model,
                **kwargs))
        else:
            super(self.__class__, self).__init__(json=json)


class Customization(InspectorComponent):
    def __init__(self, json, **kwargs):
        self.components = []
        if not json:
            super(self.__class__, self).__init__(json=dict(
                components=[]
            ))
        else:
            assert isinstance(json, dict), "json needs to be deserialised as a dictionary first, use `json.loads()`"
            assert 'components' in json, "Customization need a 'components' key in the json, got {}".format(json)
            assert isinstance(json.get('components'), (list, tuple)), \
                "Customization need a list of 'components', got {}".format(type(json.get('components')))
            for component_json in json.get('components'):
                self.components.append(InspectorComponent(json=component_json))
            self.validate()

    def add_component(self, component):
        assert isinstance(component, InspectorComponent), \
            "Component need to be of instance InspectorComponent or an object based on InspectorComponent, " \
            "got {}".format(type(component))
        self.components.append(component)

    def validate(self):
        from jsonschema import validate
        return validate(self.as_dict(), widgetconfig_json_schema)

    def as_dict(self):
        return dict(components=[component.as_dict() for component in self.components])

    def as_json(self):
        return json.dumps(self.as_dict())

    def __repr__(self):
        return "<{} ({} comp's) at {:#x}>".format(self.__class__.__name__, len(self.components), id(self))


if __name__ == '__main__':
    with open('/home/jochem/Development/pykechain/w.json', 'r') as fd:
        widgetconfigs = json.load(fd)

    w = widgetconfigs[15]
    c = Customization(json=json.loads(w))
    c.validate()
    c.as_dict()
    c.as_json()

    i = -1
    for w in widgetconfigs:
        i += 1
        try:
            c = Customization(json=json.loads(w))
            print(i, c)

        except Exception as e:
            print("EEE - got {}".format(e))
    pass

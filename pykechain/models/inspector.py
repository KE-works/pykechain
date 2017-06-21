import json

from pykechain.enums import ComponentXType
from pykechain.models import Base

uuid_pattern = "^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$"
uuid_string = {"type": "string", "pattern": uuid_pattern}
component_json_schema = {
    "$schema": "http://json-schema.org/draft-04/schema#",
    "title": "Component JSON Schema",
    "type": "object",
    "properties": {
        "xtype": {
            "type": "string",
            "enum": [ComponentXType.PROPERTYGRID, ComponentXType.SUPERGRID, "panel", "iframe",
                     ComponentXType.FILTEREDGRID, ComponentXType.PAGINATEDSUPERGRID]
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

    def __repr__(self):
        return "<{} ({}) at {:#x}>".format(self.__class__.__name__, self.xtype, id(self))


class PropertyGrid(InspectorComponent):
    def __init__(self, json=None, part=None, title=None, **kwargs):
        """
        Instantiate a PropertyGrid.

        Provide either json or (parent and model or activity)

        :param json: provide a valid json (optional if not part)
        :param part: provide a part id (or pykechain Part) (optional if json)
        :param kwargs: Optional Extras
        """
        if not json and part:
            if isinstance(part, Base):
                part = part.id
            super(self.__class__, self).__init__(json=dict(
                xtype=ComponentXType.PROPERTYGRID,
                filter=dict(part=part),
                **kwargs))
        elif json and not part:
            super(self.__class__, self).__init__(json=json)
        else:
            raise Exception("Either provide json or (parent and model)")

        if title:
            self._json_data['title'] = title
            self._json_data['viewModel'] = {'data': {'style': {'displayPartTitle': True}}}


class SuperGrid(InspectorComponent):
    """The SuperGird component."""

    def __init__(self, json=None, parent=None, model=None, activity_id=None, title=None, **kwargs):
        """
        Instantiate a SuperGrid.

        Provide either json or (parent and model or activity)

        in kwargs you may: "newInstance" in kwargs or "edit" in kwargs or "delete" in kwargs or "export" in kwargs

        :param json: provide a valid SuperGrid json (optional if not parent & model)
        :param parent: provide a parent id (or pykechain Part) (optional if json)
        :param model: provide a model id (or pykechain Part) (optional if json)
        :param activity_id: provide a acitivity id (or pykechain Activity) (optional)
        :param title: adding title to the component (optional)
        :param newInstance: boolean to show button
        :param edit: boolean to show button
        :param delete: boolean to show button
        :param export: boolean to show button
        :param kwargs: Optional extra kwargs.
        """
        if not json and parent and model:
            if isinstance(parent, Base):
                parent = parent.id
            if isinstance(model, Base):
                model = model.id
            if isinstance(activity_id, Base):
                activity_id = activity_id.id
            super(self.__class__, self).__init__(json=dict(
                xtype=ComponentXType.SUPERGRID,
                filter=dict(parent=parent, model=model, activity_id=activity_id),
                **kwargs))
        elif json and not parent and not model:
            super(self.__class__, self).__init__(json=json)
        else:
            raise Exception("Either provide json or (parent and model)")

        if title:
            self._json_data['title'] = title

        # check for buttons
        if "newInstance" in kwargs or "edit" in kwargs or "delete" in kwargs or "export" in kwargs:
            self._json_data['viewModel'] = {'data': {"actions": {
                "newInstance": kwargs.get("newInstance", False),
                "edit": kwargs.get("edit", False),
                "delete": kwargs.get("delete", False),
                "export": kwargs.get("export", False)
            }}}

    def get(self, item):
        """Get an item from the filter subdict.

        :param item: item to retrieve. eg. model, parent, activity_id
        :return: uuid (as string)
        """
        return self._json_data['filter'].get(item, None)

    def set(self, key, value):
        """Set an item to a value in the filter subdictionary.

        :param key: string to set e.g model, parent, activity_id
        :param value: UUID as string or an pykechain object (will retrieve the id from that)
        :return: None
        """
        if isinstance(value, Base):
            value = value.id
        self._json_data['filter'][key] = value


class Customization(InspectorComponent):
    """Customization wrapper object."""

    def __init__(self, json=None, **kwargs):
        """Make a new Customization object that wraps the various components.

        :param json: (optional) provide a Customization json, will be validated
        :ivar components: list of components
        """
        self.components = []
        if json:
            assert isinstance(json, dict), "json needs to be deserialised as a dictionary first, use `json.loads()`"
            assert 'components' in json, "Customization need a 'components' key in the json, got {}".format(json)
            assert isinstance(json.get('components'), (list, tuple)), \
                "Customization need a list of 'components', got {}".format(type(json.get('components')))
            for component_json in json.get('components'):
                self.components.append(InspectorComponent(json=component_json))
            self.validate()

    def add_component(self, component):
        """Add a component to the internal components list."""
        assert isinstance(component, InspectorComponent), \
            "Component need to be of instance InspectorComponent or an object based on InspectorComponent, " \
            "got {}".format(type(component))
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

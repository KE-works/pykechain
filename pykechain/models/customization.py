import requests
from jsonschema import validate

from pykechain.enums import ComponentXType, Category
from pykechain.exceptions import APIError

uuid_pattern = r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$"
uuid_string = {"type": "string", "pattern": uuid_pattern}
component_json_schema = {
    "$schema": "http://json-schema.org/draft-04/schema#",
    "title": "Component JSON Schema",
    "type": "object",
    "properties": {
        "xtype": {
            "type": "string",
            "enum": ComponentXType.values()
        },
        "filter": {
            "type": "object",
            "properties": {
                "part": uuid_string,
                "model": uuid_string,
                "parent": uuid_string,
                "part_id": uuid_string,
                "model_id": uuid_string,
                "parent_id": uuid_string
            }
        },
        "title": {"type": ["string", "null"]},
        "viewModel": {"type": "object"},
        "model": uuid_string,
        "parent": uuid_string
    },
    "required": ["xtype"]
}
widgetconfig_json_schema = {
    "$schema": "http://json-schema.org/draft-04/schema#",
    "title": "WidgetConfig JSON",
    "type": "object",
    "properties": {
        "ext": {
            "type": "object",
            "widgets": {
                "type": "array",
                "items": component_json_schema
            }
        }
    }
}


class CustomizationBase(object):
    """Base class for customization objects.

    :cvar activity: the :class:`Activity`
    """

    def __init__(self, activity, client):
        """Initialize the Base class for customization objects."""
        self._client = client
        self.activity = activity


class ExtCustomization(CustomizationBase):
    """A class to represent the activity customization for Ext Js."""

    def __str__(self):  # pragma: no cover
        return "<pyke ExtCustomization '{}' id {} ({} widgets)>".format(
            self.activity.name, str(self.activity.id)[-8:], len(self.widgets()))

    def __repr__(self):  # pragma: no cover
        return self.__str__()

    def _save_customization(self, widgets):
        """
        Save the complete customization to the activity.

        :param widgets: The complete set of widgets to be customized
        """
        if len(widgets) > 0:
            # Get the current customization and only replace the 'ext' part of it
            customization = self.activity._json_data.get('customization', dict())
            if customization:
                customization['ext'] = dict(widgets=widgets)
            else:
                customization = dict(ext=dict(widgets=widgets))

        # Empty the customization if if the widgets list is empty
        else:
            customization = None

        # perform validation
        if customization:
            validate(customization, widgetconfig_json_schema)

        # Save to the activity and store the saved activity to self
        response = self._client._request("PUT",
                                         self._client._build_url("activity", activity_id=str(self.activity.id)),
                                         json=dict(customization=customization))
        if response.status_code != requests.codes.ok:  # pragma: no cover
            raise APIError("Could not save customization ({})".format(response))
        else:
            # refresh the activity json
            self.activity = self._client.activity(pk=self.activity.id)

    def _add_widget(self, widget):
        """
        Add a widget to the customization.

        Will save the widget to KE-chain.

        :param widget: The widget (specific json dict) to be added
        :type widget: dict
        """
        widgets = self.widgets()
        widgets += [widget]
        self._save_customization(widgets)

    def widgets(self):
        """
        Get the Ext JS specific customization from the activity.

        :return: The Ext JS specific customization in `list(dict)` form
        """
        customization = self.activity._json_data.get('customization')

        if customization and "ext" in customization.keys():
            return customization['ext']['widgets']
        else:
            return []

    def delete_widget(self, index):
        """
        Delete widgets by index.

        The widgets are saved to KE-chain.

        :param index: The index of the widget to be deleted in the self.widgets
        :type index: int
        :raises ValueError: if the customization has no widgets
        """
        widgets = self.widgets()
        if len(widgets) is 0:
            raise ValueError("This customization has no widgets")
        widgets.pop(index)
        self._save_customization(widgets)

    def delete_all_widgets(self):
        """Delete all widgets.

        :raises APIError: if the widgets could not be deleted.
        """
        self._save_customization([])

    def add_json_widget(self, config):
        """
        Add an Ext Json Widget to the customization.

        The configuration json provided must be interpretable by KE-chain. The json will be validated
        against the widget json schema.

        The widget will be saved to KE-chain.

        :param config: The json configuration of the widget
        :type config: dict
        """
        validate(config, component_json_schema)
        self._add_widget(dict(config=config, name="jsonWidget"))

    def add_property_grid_widget(self, part_instance, max_height=None, custom_title=None):
        """
        Add an KE-chain Property Grid widget to the customization.

        The widget will be saved to KE-chain.

        :param part_instance: The part instance on which the property grid will be based
        :type part_instance: :class:`Part`
        :param max_height: The max height of the property grid in pixels
        :type max_height: int or None
        :param custom_title: A custom title for the property grid
                 - None (default): Part instance name
                 - String value: Custom title
                 - False: No title
        :type custom_title: basestring or None
        """
        # Declare property grid config
        config = {
            "xtype": ComponentXType.PROPERTYGRID,
            "category": Category.INSTANCE,
            "filter": {
                "activity_id": str(self.activity.id),
                "part": str(part_instance.id)
            }
        }

        # Add max height and custom title
        if max_height:
            config['maxHeight'] = max_height
        if custom_title is None:
            show_title_value = "Default"
            title = part_instance.name
        elif custom_title:
            show_title_value = "Custom Title"
            title = str(custom_title)
        else:
            show_title_value = "No title"
            title = None
        config["title"] = title

        # Declare the meta info for the property grid
        meta = {
            "activityId": str(self.activity.id),
            "customHeight": max_height if max_height else None,
            "customTitle": title,
            "partInstanceId": str(part_instance.id),
            "showHeightValue": "Custom max height" if max_height else "Auto",
            "showTitleValue": show_title_value
        }

        self._add_widget(dict(config=config, meta=meta, name='propertyGridWidget'))

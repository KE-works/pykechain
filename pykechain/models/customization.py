import requests
from jsonschema import validate

from pykechain.enums import ComponentXType, Category, SortTable
from pykechain.exceptions import APIError, IllegalArgumentError

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

    def add_super_grid_widget(self, part_model, delete=False, edit=True, export=True, incomplete_rows=True,
                              new_instance=False, parent_part_instance=None, max_height=None, custom_title=False,
                              emphasize_edit=False, emphasize_new_instance=True, sort_property=None,
                              sort_direction=SortTable.ASCENDING):
        """
        Add an KE-chain superGrid (e.g. basic table) widget to the customization.

        The widget will be saved to KE-chain.

        :param emphasize_new_instance:
        :type emphasize_new_instance: bool
        :param emphasize_edit:
        :type emphasize_edit: bool
        :param new_instance:
        :type new_instance: bool
        :param incomplete_rows:
        :type incomplete_rows: bool
        :param export:
        :type export: bool
        :param edit:
        :type edit: bool
        :param delete:
        :type delete: bool
        :param part_model: The part model based on which all instances will be shown.
        :type parent_part_instance: :class:`Part`
        :param parent_part_instance: The parent part instance for which the instances will be shown or to which new
        instances will be added.
        :type parent_part_instance: :class:`Part`
        :param max_height: The max height of the supergrid in pixels
        :type max_height: int or None
        :param custom_title: A custom title for the supergrid
                 - False (default): Part instance name
                 - String value: Custom title
                 - None: No title
        :type custom_title: basestring or None
        :param sort_property: The property model on which the part instances are being sorted on
        :type sort_property: :class:`Property`
        :param sort_direction: The direction on which the values of property instances are being sorted on
        :type sort_direction: basestring (see enums)
                  - ASC (default): Sort in ascending order
                  - DESC: Sort in descending order
        """
        # Assertions
        if not parent_part_instance and new_instance:
            raise IllegalArgumentError("If you want to allow the creation of new part instances, you must specify a "
                                       "parent_part_instance")
        if sort_property and sort_property.part.id != part_model.id:
            raise IllegalArgumentError("If you want to sort on a property, then sort_property must be located under "
                                       "part_model")
        # Declare supergrid config
        config = {
            "xtype": ComponentXType.SUPERGRID,
            "filter": {
                "activity_id": str(self.activity.id),
                "model": str(part_model.id)
            },
            "viewModel": {
                "data": {
                    "actions": {
                        "delete": delete,
                        "edit": edit,
                        "export": export,
                        "incompleteRows": incomplete_rows,
                        "newInstance": new_instance
                    },
                    "sorters": [{
                        "direction": sort_direction,
                        "property": sort_property.id
                    }] if sort_property else [],
                    "ui": {
                        "newInstance": "primary-action" if emphasize_new_instance else "default-toolbar",
                        "edit": "primary-action" if emphasize_edit else "default-toolbar"
                    }
                }
            }
        }

        # Add parent to filter if added.
        if parent_part_instance:
            config['filter']["parent"] = str(parent_part_instance.id)
            parent_instance_id = str(parent_part_instance.id)
        else:
            parent_instance_id = None
        # Add max height and custom title
        if max_height:
            config['maxHeight'] = max_height

        if custom_title is False:
            show_title_value = "Default"
            title = part_model.name
        elif custom_title is None:
            show_title_value = "No title"
            title = None
        else:
            show_title_value = "Custom Title"
            title = str(custom_title)

        config["title"] = title
        config["showTitleValue"] = show_title_value

        # Declare the meta info for the supergrid
        meta = {
            "parentInstanceId": parent_instance_id,
            "editButtonUi": "primary-action" if emphasize_edit else "default-toolbar",
            "customHeight": max_height if max_height else 500,
            "primaryAddUiValue": emphasize_new_instance,
            "activityId": str(self.activity.id),
            "customTitle": title,
            "primaryEditUiValue": emphasize_edit,
            "downloadButtonVisible": export,
            "addButtonUi": "primary-action" if emphasize_new_instance else "default-toolbar",
            "deleteButtonVisible": delete,
            "incompleteRowsButtonVisible": incomplete_rows,
            "addButtonVisible": new_instance,
            "showTitleValue": show_title_value,
            "partModelId": str(part_model.id),
            "editButtonVisible": edit,
            "showHeightValue": "Custom max height" if max_height else "Auto",
            'sortDirection': sort_direction,
            'sortedColumn': sort_property.id if sort_property else None
        }

        self._add_widget(dict(config=config, meta=meta, name='superGridWidget'))

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

    def add_text_widget(self, text=None, custom_title=None, collapsible=False):
        """
        Add an KE-chain Property Text widget to the customization.

        The widget will be saved to KE-chain.

        :param text: The text that will be shown by the widget.
        :type text: basestring or None
        :param custom_title: A custom title for the text panel
                 - None (default): No title
                 - String value: Custom title
        :type custom_title: basestring or None
        :param collapsible: A boolean to decide whether the panel is collapsible or not
        :type collapsible: bool
        """
        # Declare text widget config
        config = {
            "xtype": ComponentXType.HTMLPANEL,
            "filter": {
                "activity_id": str(self.activity.id),
            }
        }

        # Add text and custom title
        if text:
            config['html'] = text
        if custom_title:
            show_title_value = "Custom Title"
            title = custom_title
        else:
            show_title_value = "No Title"
            title = None
        config['collapsible'] = collapsible
        config['title'] = title
        # Declare the meta info for the property grid
        meta = {
            "activityId": str(self.activity.id),
            "customTitle": title,
            "collapsible": collapsible,
            "html": text,
            "showTitleValue": show_title_value
        }

        self._add_widget(dict(config=config, meta=meta, name='htmlWidget'))

    # def add_
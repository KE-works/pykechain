import requests
from jsonschema import validate
from six import text_type

from pykechain.enums import ComponentXType, Category, SortTable, PropertyType, NavigationBarAlignment, WidgetNames, \
    ShowColumnTypes
from pykechain.exceptions import APIError, IllegalArgumentError
from pykechain.models.activity import Activity
from pykechain.models.part import Part
from pykechain.models.property import Property
from pykechain.models.service import Service
from pykechain.utils import is_uuid

uuid_pattern = r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$"
uuid_string = {"type": "string", "pattern": uuid_pattern}

# deprecated as we are moving towards a 'meta' definition for the widgets in KE-chain 3
# only for checking the jsonwidget
component_jsonwidget_schema = {
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

widget_json_stub = {
    "title": "Widget JSON schema",
    "type": "object",
    "required": ["name", "meta"],
    "properties": {
        "name": {"type": "string", "enum": WidgetNames.values()},
        "meta": {"type": "object"},
        "config": {"type": "object"}
    }
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
                "items": widget_json_stub
            }
        }
    }
}


class CustomizationBase(object):
    """Base class for customization objects.

    :cvar activity: an instance of :class:`pykechain.models.Activity`
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
        validate(config, component_jsonwidget_schema)
        self._add_widget(dict(config=config, name=WidgetNames.JSONWIDGET))

    def add_super_grid_widget(self, part_model, delete=False, edit=True, export=True, incomplete_rows=True,
                              new_instance=False, parent_part_instance=None, max_height=None, custom_title=False,
                              emphasize_edit=False, emphasize_new_instance=True, sort_property=None,
                              sort_direction=SortTable.ASCENDING):
        """
        Add a KE-chain superGrid (e.g. basic table widget) to the customization.

        The widget will be saved to KE-chain.

        :param emphasize_new_instance: Emphasize the New instance button (default True)
        :type emphasize_new_instance: bool
        :param emphasize_edit: Emphasize the Edit button (default False)
        :type emphasize_edit: bool
        :param new_instance: Show or hide the New instance button (default False). You need to provide a
            `parent_part_instance` in order for this to work.
        :type new_instance: bool
        :param incomplete_rows: Show or hide the Incomplete Rows filter button (default True)
        :type incomplete_rows: bool
        :param export: Show or hide the Export Grid button (default True)
        :type export: bool
        :param edit: Show or hide the Edit button (default True)
        :type edit: bool
        :param delete: Show or hide the Delete button (default False)
        :type delete: bool
        :param part_model: The part model based on which all instances will be shown.
        :type parent_part_instance: :class:`Part` or UUID
        :param parent_part_instance: The parent part instance for which the instances will be shown or to which new
            instances will be added.
        :type parent_part_instance: :class:`Part` or UUID
        :param max_height: The max height of the supergrid in pixels
        :type max_height: int or None
        :param custom_title: A custom title for the supergrid::
            * False (default): Part instance name
            * String value: Custom title
            * None: No title
        :type custom_title: bool or basestring or None
        :param sort_property: The property model on which the part instances are being sorted on
        :type sort_property: :class:`Property` or UUID
        :param sort_direction: The direction on which the values of property instances are being sorted on:
            * ASC (default): Sort in ascending order
            * DESC: Sort in descending order
        :type sort_direction: basestring (see :class:`enums.SortTable`)
        :raises IllegalArgumentError: When unknown or illegal arguments are passed.

        """
        # Check whether the part_model is uuid type or class `Part`
        if isinstance(part_model, Part):
            part_model_id = part_model.id
        elif isinstance(part_model, text_type) and is_uuid(part_model):
            part_model_id = part_model
            part_model = self._client.model(id=part_model_id)
        else:
            raise IllegalArgumentError("When using the add_super_grid_widget, part_model must be a Part or Part id. "
                                       "Type is: {}".format(type(part_model)))

        # Check whether the parent_part_instance is uuid type or class `Part`
        if isinstance(parent_part_instance, Part):
            parent_part_instance_id = parent_part_instance.id
        elif isinstance(parent_part_instance, text_type) and is_uuid(parent_part_instance):
            parent_part_instance_id = parent_part_instance
            parent_part_instance = self._client.part(id=parent_part_instance_id)
        elif isinstance(parent_part_instance, type(None)):
            parent_part_instance_id = None
        else:
            raise IllegalArgumentError("When using the add_super_grid_widget, parent_part_instance must be a "
                                       "Part, Part id or None. Type is: {}".format(type(parent_part_instance)))

        # Check whether the sort_property is uuid type or class `Property`
        if isinstance(sort_property, Property):
            sort_property_id = sort_property.id
        elif isinstance(sort_property, text_type) and is_uuid(sort_property):
            sort_property_id = sort_property
            sort_property = self._client.property(id=sort_property_id, category=Category.MODEL)
        elif isinstance(sort_property, type(None)):
            sort_property_id = None
        else:
            raise IllegalArgumentError("When using the add_super_grid_widget, sort_property must be a "
                                       "Property, Property id or None. Type is: {}".format(type(sort_property)))

        # Assertions
        if not parent_part_instance and new_instance:
            raise IllegalArgumentError("If you want to allow the creation of new part instances, you must specify a "
                                       "parent_part_instance")
        if sort_property and sort_property.part.id != part_model.id:
            raise IllegalArgumentError("If you want to sort on a property, then sort_property must be located under "
                                       "part_model")
        # Declare superGrid config
        config = {
            "xtype": ComponentXType.SUPERGRID,
            "filter": {
                "activity_id": str(self.activity.id),
                "model": part_model_id
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
                        "property": sort_property_id
                    }] if sort_property_id else [],
                    "ui": {
                        "newInstance": "primary-action" if emphasize_new_instance else "default-toolbar",
                        "edit": "primary-action" if emphasize_edit else "default-toolbar"
                    }
                }
            }
        }

        # Add parent to filter if added.
        config['filter']["parent"] = parent_part_instance_id

        # Add max height and custom title
        if max_height:
            config['maxHeight'] = max_height

        if custom_title is False:
            show_title_value = "Default"
            title = part_model.name
        elif custom_title is None:
            show_title_value = "No title"
            title = str()
        else:
            show_title_value = "Custom Title"
            title = str(custom_title)

        config["title"] = title
        config["showTitleValue"] = show_title_value

        # Declare the meta info for the superGrid
        meta = {
            "parentInstanceId": parent_part_instance_id,
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
            "partModelId": part_model_id,
            "editButtonVisible": edit,
            "showHeightValue": "Custom max height" if max_height else "Auto",
            "sortDirection": sort_direction,
            "sortedColumn": sort_property_id if sort_property_id else None
        }

        self._add_widget(dict(config=config, meta=meta, name=WidgetNames.SUPERGRIDWIDGET))

    def add_property_grid_widget(self, part_instance, max_height=None, custom_title=False, show_headers=True,
                                 show_columns=None):
        """
        Add a KE-chain Property Grid widget to the customization.

        The widget will be saved to KE-chain.

        :param part_instance: The part instance on which the property grid will be based
        :type part_instance: :class:`Part` or UUID
        :param max_height: The max height of the property grid in pixels
        :type max_height: int or None
        :param custom_title: A custom title for the property grid::
            * False (default): Part instance name
            * String value: Custom title
            * None: No title
        :type custom_title: bool or basestring or None
        :param show_headers: Show or hide the headers in the grid (default True)
        :type show_headers: bool
        :param show_columns: Columns to be hidden or shown (default to 'unit' and 'description')
        :type show_columns: list
        :raises IllegalArgumentError: When unknown or illegal arguments are passed.
        """
        # Check whether the parent_part_instance is uuid type or class `Part`
        if isinstance(part_instance, Part):
            part_instance_id = part_instance.id
        elif isinstance(part_instance, text_type) and is_uuid(part_instance):
            part_instance_id = part_instance
            part_instance = self._client.part(id=part_instance_id)
        else:
            raise IllegalArgumentError("When using the add_property_grid_widget, part_instance must be a "
                                       "Part or Part id. Type is: {}".format(type(part_instance)))
        if not show_columns:
            show_columns = list()

        # Set the display_columns for the config
        possible_columns = [ShowColumnTypes.DESCRIPTION, ShowColumnTypes.UNIT]
        display_columns = dict()

        for possible_column in possible_columns:
            if possible_column in show_columns:
                display_columns[possible_column] = True
            else:
                display_columns[possible_column] = False

        # Declare property grid config
        config = {
            "xtype": ComponentXType.PROPERTYGRID,
            "category": Category.INSTANCE,
            "filter": {
                "activity_id": str(self.activity.id),
                "part": part_instance_id
            },
            "hideHeaders": not show_headers,
            "viewModel": {
                "data": {
                    "displayColumns": display_columns
                }
            }
        }

        # Add max height and custom title
        if max_height:
            config['maxHeight'] = max_height

        if custom_title is False:
            show_title_value = "Default"
            title = part_instance.name
        elif custom_title is None:
            show_title_value = "No title"
            title = str()
        else:
            show_title_value = "Custom Title"
            title = str(custom_title)

        config["title"] = title

        # Declare the meta info for the property grid
        meta = {
            "activityId": str(self.activity.id),
            "customHeight": max_height if max_height else None,
            "customTitle": title,
            "partInstanceId": part_instance_id,
            "showColumns": show_columns,
            "showHeaders": show_headers,
            "showHeightValue": "Custom max height" if max_height else "Auto",
            "showTitleValue": show_title_value
        }

        self._add_widget(dict(config=config, meta=meta, name=WidgetNames.PROPERTYGRIDWIDGET))

    def add_text_widget(self, text=None, custom_title=None, collapsible=True, collapsed=False):
        """
        Add a KE-chain Text widget to the customization.

        The widget will be saved to KE-chain.

        :param text: The text that will be shown by the widget.
        :type text: basestring or None
        :param custom_title: A custom title for the text panel::
            * None (default): No title
            * String value: Custom title
        :type custom_title: basestring or None
        :param collapsible: A boolean to decide whether the panel is collapsible or not (default True)
        :type collapsible: bool
        :param collapsed: A boolean to decide whether the panel is collapsed or not (default False)
        :type collapsible: bool
        :raises IllegalArgumentError: When unknown or illegal arguments are passed.
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
        # A widget can only be collapsed if it is collapsible in the first place
        if collapsible:
            config['collapsed'] = collapsed
        else:
            config['collapsed'] = False
        config['title'] = title
        # Declare the meta info for the property grid
        meta = {
            "activityId": str(self.activity.id),
            "customTitle": title,
            "collapsible": collapsible,
            "collapsed": collapsed,
            "html": text,
            "showTitleValue": show_title_value
        }

        self._add_widget(dict(config=config, meta=meta, name=WidgetNames.HTMLWIDGET))

    def add_paginated_grid_widget(self, part_model, delete=False, edit=True, export=True,
                                  new_instance=False, parent_part_instance=None, max_height=None, custom_title=False,
                                  emphasize_edit=False, emphasize_new_instance=True, sort_property=None,
                                  sort_direction=SortTable.ASCENDING, page_size=25, collapse_filters=False):
        """
        Add a KE-chain paginatedGrid (e.g. paginated table widget) to the customization.

        The widget will be saved to KE-chain.

        :param emphasize_new_instance: Emphasize the New instance button (default True)
        :type emphasize_new_instance: bool
        :param emphasize_edit: Emphasize the Edit button (default False)
        :type emphasize_edit: bool
        :param new_instance: Show or hide the New instance button (default False). You need to provide a
            `parent_part_instance` in order for this to work.
        :type new_instance: bool
        :param incomplete_rows: Show or hide the Incomplete Rows filter button (default True)
        :type incomplete_rows: bool
        :param export: Show or hide the Export Grid button (default True)
        :type export: bool
        :param edit: Show or hide the Edit button (default True)
        :type edit: bool
        :param delete: Show or hide the Delete button (default False)
        :type delete: bool
        :param page_size: Number of parts that will be shown per page in the grid.
        :type page_size: int
        :param collapse_filters: Hide or show the filters pane (default False)
        :type collapse_filters: bool
        :param part_model: The part model based on which all instances will be shown.
        :type parent_part_instance: :class:`Part` or UUID
        :param parent_part_instance: The parent part instance for which the instances will be shown or to which new
            instances will be added.
        :type parent_part_instance: :class:`Part` or UUID
        :param max_height: The max height of the paginated grid in pixels
        :type max_height: int or None
        :param custom_title: A custom title for the paginated grid::
            * False (default): Part instance name
            * String value: Custom title
            * None: No title
        :type custom_title: bool or basestring or None
        :param sort_property: The property model on which the part instances are being sorted on
        :type sort_property: :class:`Property` or UUID
        :param sort_direction: The direction on which the values of property instances are being sorted on::
            * ASC (default): Sort in ascending order
            * DESC: Sort in descending order
        :type sort_direction: basestring (see :class:`enums.SortTable`)
        :raises IllegalArgumentError: When unknown or illegal arguments are passed.
        """
        # Check whether the part_model is uuid type or class `Part`
        if isinstance(part_model, Part):
            part_model_id = part_model.id
        elif isinstance(part_model, text_type) and is_uuid(part_model):
            part_model_id = part_model
            part_model = self._client.model(id=part_model_id)
        else:
            raise IllegalArgumentError("When using the add_paginated_grid_widget, part_model must be a Part or Part id."
                                       " Type is: {}".format(type(part_model)))

        # Check whether the parent_part_instance is uuid type or class `Part`
        if isinstance(parent_part_instance, Part):
            parent_part_instance_id = parent_part_instance.id
        elif isinstance(parent_part_instance, text_type) and is_uuid(parent_part_instance):
            parent_part_instance_id = parent_part_instance
            parent_part_instance = self._client.part(id=parent_part_instance_id)
        elif isinstance(parent_part_instance, type(None)):
            parent_part_instance_id = None
        else:
            raise IllegalArgumentError("When using the add_paginated_grid_widget, parent_part_instance must be a "
                                       "Part, Part id or None. Type is: {}".format(type(parent_part_instance)))

        # Check whether the sort_property is uuid type or class `Property`
        if isinstance(sort_property, Property):
            sort_property_id = sort_property.id
        elif isinstance(sort_property, text_type) and is_uuid(sort_property):
            sort_property_id = sort_property
            sort_property = self._client.property(id=sort_property_id, category=Category.MODEL)
        elif isinstance(sort_property, type(None)):
            sort_property_id = None
        else:
            raise IllegalArgumentError("When using the add_paginated_grid_widget, sort_property must be a "
                                       "Property, Property id or None. Type is: {}".format(type(sort_property)))

        # Assertions
        if not parent_part_instance and new_instance:
            raise IllegalArgumentError("If you want to allow the creation of new part instances, you must specify a "
                                       "parent_part_instance")
        if sort_property and sort_property.part.id != part_model.id:
            raise IllegalArgumentError("If you want to sort on a property, then sort_property must be located under "
                                       "part_model")

        # Add custom title
        if custom_title is False:
            show_title_value = "Default"
            title = part_model.name
        elif custom_title is None:
            show_title_value = "No title"
            title = ' '
        else:
            show_title_value = "Custom Title"
            title = str(custom_title)

        # Set the collapse filters value
        if collapse_filters:
            collapse_filters_value = "Collapsed"
        else:
            collapse_filters_value = "Expanded"

        # Declare paginatedGrid config
        config = {
            "xtype": ComponentXType.FILTEREDGRID,
            "filter": {
                "activity_id": str(self.activity.id),
            },
            "grid": {
                "viewModel": {
                    "data": {
                        "actions": {
                            "delete": delete,
                            "edit": edit,
                            "export": export,
                            "newInstance": new_instance
                        },
                        "sorters": [{
                            "direction": sort_direction,
                            "property": sort_property_id
                        }] if sort_property_id else [],
                        "ui": {
                            "newInstance": "primary-action" if emphasize_new_instance else "default-toolbar",
                            "edit": "primary-action" if emphasize_edit else "default-toolbar"
                        },
                        "pageSize": page_size
                    }
                },
                "xtype": ComponentXType.PAGINATEDSUPERGRID,
                "title": title,
                "showTitleValue": show_title_value,
            },
            "maxHeight": max_height if max_height else None,
            "parentInstanceId": parent_part_instance_id,
            "partModelId": part_model_id,
            "collapseFilters": collapse_filters
        }

        # Declare the meta info for the paginatedGrid
        meta = {
            "parentInstanceId": parent_part_instance_id,
            "editButtonUi": "primary-action" if emphasize_edit else "default-toolbar",
            "editButtonVisible": edit,
            "customHeight": max_height if max_height else 500,
            "primaryAddUiValue": emphasize_new_instance,
            "activityId": str(self.activity.id),
            "customTitle": title,
            "primaryEditUiValue": emphasize_edit,
            "downloadButtonVisible": export,
            "addButtonUi": "primary-action" if emphasize_new_instance else "default-toolbar",
            "deleteButtonVisible": delete,
            "addButtonVisible": new_instance,
            "showTitleValue": show_title_value,
            "partModelId": str(part_model_id),
            "showHeightValue": "Custom max height" if max_height else "Auto",
            "sortDirection": sort_direction,
            "sortedColumn": sort_property_id if sort_property_id else None,
            "collapseFilters": collapse_filters,
            "showCollapseFiltersValue": collapse_filters_value,
            "customPageSize": page_size
        }

        self._add_widget(dict(config=config, meta=meta, name=WidgetNames.FILTEREDGRIDWIDGET))

    def add_script_widget(self, script, custom_title=False, custom_button_text=False, emphasize_run=True):
        """
        Add a KE-chain Script (e.g. script widget) to the customization.

        The widget will be saved to KE-chain.

        :param script: The Script to which the button will be coupled and will be ran when the button is pressed.
        :type script: :class:`Service` or UUID
        :param custom_title: A custom title for the script widget
            * False (default): Script name
            * String value: Custom title
            * None: No title
        :type custom_title: bool or basestring or None
        :param custom_button_text: A custom text for the button linked to the script
            * False (default): Script name
            * String value: Custom title
            * None: No title
        :type custom_button_text: bool or basestring or None
        :param emphasize_run: Emphasize the run button (default True)
        :type emphasize_run: bool
        :raises IllegalArgumentError: When unknown or illegal arguments are passed.
        """
        # Check whether the script is uuid type or class `Service`
        if isinstance(script, Service):
            script_id = script.id
        elif isinstance(script, text_type) and is_uuid(script):
            script_id = script
            script = self._client.service(id=script_id)
        else:
            raise IllegalArgumentError("When using the add_script_widget, script must be a Service or Service id. "
                                       "Type is: {}".format(type(script)))
        # Add custom title
        if custom_title is False:
            show_title_value = "Default"
            title = script.name
        elif custom_title is None:
            show_title_value = "No title"
            title = ''
        else:
            show_title_value = "Custom Title"
            title = str(custom_title)

        # Add custom button text
        if custom_button_text is False:
            show_button_value = "Default"
            button_text = script.name
        elif custom_button_text is None:
            show_button_value = "No title"
            button_text = ''
        else:
            show_button_value = "Custom Title"
            button_text = str(custom_button_text)

        # Declare script widget config
        config = {
            'showTitleValue': show_title_value,
            'serviceId': script_id,
            'viewModel': {
                'data': {
                    'buttonUI': 'primary-action' if emphasize_run else "default-toolbar",
                }
            },
            'title': title,
            'xtype': ComponentXType.EXECUTESERVICE,
            'customButtonText': button_text
        }

        # Declare script widget meta
        meta = {
            'showButtonValue': show_button_value,
            'customText': button_text,
            'customTitle': title,
            'serviceId': script_id,
            'emphasizeButton': emphasize_run,
            'showTitleValue': show_title_value
        }

        self._add_widget(dict(config=config, meta=meta, name=WidgetNames.SERVICEWIDGET))

    def add_notebook_widget(self, notebook, custom_title=False, height=None):
        """
        Add a KE-chain Notebook (e.g. notebook widget) to the customization.

        The widget will be saved to KE-chain.

        :param notebook: The Notebook to which the button will be coupled and will start when the button is pressed.
        :type notebook: :class:`Service` or UUID
        :param custom_title: A custom title for the notebook widget
            * False (default): Notebook name
            * String value: Custom title
            * None: No title
        :type custom_title: bool or basestring or None
        :param height: The height of the Notebook in pixels
        :type height: int or None
        :raises IllegalArgumentError: When unknown or illegal arguments are passed.
        """
        # Check whether the script is uuid type or class `Service`
        if isinstance(notebook, Service):
            notebook_id = notebook.id
        elif isinstance(notebook, text_type) and is_uuid(notebook):
            notebook_id = notebook
            notebook = self._client.service(id=notebook_id)
        else:
            raise IllegalArgumentError("When using the add_notebook_widget, notebook must be a Service or Service id. "
                                       "Type is: {}".format(type(notebook)))

        # Add custom title
        if custom_title is False:
            show_title_value = "Default"
            title = notebook.name
        elif custom_title is None:
            show_title_value = "No title"
            title = ''
        else:
            show_title_value = "Custom Title"
            title = str(custom_title)

        # Declare notebook widget config
        config = {
            'title': title,
            'showTitleValue': show_title_value,
            'height': height if height else 800,
            'xtype': ComponentXType.NOTEBOOKPANEL,
            'serviceId': notebook_id
        }

        # Declare notebook widget meta
        meta = {
            'showTitleValue': show_title_value,
            'customHeight': height if height else 800,
            'customTitle': title,
            'serviceId': notebook_id
        }

        self._add_widget(dict(config=config, meta=meta, name=WidgetNames.NOTEBOOKWIDGET))

    def add_attachment_viewer_widget(self, attachment_property, custom_title=False, height=None):
        """
        Add a KE-chain Attachment Viewer (e.g. attachment viewer widget) to the customization.

        The widget will be saved to KE-chain.

        :param attachment_property: The Attachment Property to which the Viewer will be connected to.
        :type attachment_property: :class:`Property` or UUID
        :param custom_title: A custom title for the attachment viewer widget
            * False (default): Notebook name
            * String value: Custom title
            * None: No title
        :type custom_title: bool or basestring or None
        :param height: The height of the Notebook in pixels
        :type height: int or None
        :raises IllegalArgumentError: When unknown or illegal arguments are passed.
        """
        # Check whether the attachment property is uuid type or class `Property`
        if isinstance(attachment_property, Property):
            attachment_property_id = attachment_property.id
        elif isinstance(attachment_property, text_type) and is_uuid(attachment_property):
            attachment_property_id = attachment_property
            attachment_property = self._client.property(id=attachment_property_id)
        else:
            raise IllegalArgumentError("When using the add_attachment_viewer_widget, attachment_property must be a "
                                       "Property or Property id. Type is: {}".format(type(attachment_property)))

        # Check whether the `Property` has type `Attachment`
        property_type = attachment_property.type
        if property_type != PropertyType.ATTACHMENT_VALUE:
            raise IllegalArgumentError("When using the add_attachment_viewer_widget, attachment_property must have "
                                       "type {}. Type found: {}".format(PropertyType.ATTACHMENT_VALUE, property_type))

        # Check also whether `Property` has category `Instance`
        property_category = attachment_property._json_data['category']
        if property_category != Category.INSTANCE:
            raise IllegalArgumentError("When using the add_attachment_viewer_widget, attachment_property must have "
                                       "category {}. Category found: {}".format(Category.INSTANCE, property_category))

        # Add custom title
        if custom_title is False:
            show_title_value = "Default"
            title = attachment_property.name
        elif custom_title is None:
            show_title_value = "No title"
            title = ''
        else:
            show_title_value = "Custom Title"
            title = str(custom_title)

        # Declare attachment viewer widget config
        config = {
            'propertyId': attachment_property_id,
            'showTitleValue': show_title_value,
            'xtype': ComponentXType.PROPERTYATTACHMENTPREVIEWER,
            'title': title,
            'filter': {
                'activity_id': str(self.activity.id)
            },
            'height': height if height else 500
        }

        # Declare attachment viewer widget meta
        meta = {
            'propertyInstanceId': attachment_property_id,
            'activityId': str(self.activity.id),
            'customHeight': height if height else 500,
            'showTitleValue': show_title_value,
            'customTitle': title
        }

        self._add_widget(dict(config=config, meta=meta, name=WidgetNames.ATTACHMENTVIEWERWIDGET))

    def add_navigation_bar_widget(self, activities, alignment=NavigationBarAlignment.CENTER):
        """
        Add a KE-chain Navigation Bar (e.g. navigation bar widget) to the customization.

        The widget will be saved to KE-chain.

        :param activities: List of activities. Each activity must be a Python dict(), with the following keys:
            * customText: A custom text for each button in the attachment viewer widget: None (default): Task name;
            a String value: Custom text
            * emphasize: bool which determines if the button should stand-out or not - default(False)
            * activityId: class `Activity` or UUID
        :type activities: list
        :param alignment: The alignment of the buttons inside navigation bar
            * center (default): Center aligned
            * start: left aligned
        :type alignment: basestring (see :class:`enums.NavigationBarAlignment`)

        :raises IllegalArgumentError: When unknown or illegal arguments are passed.
        """
        # Loop through the list of activities
        set_of_expected_keys = {'activityId', 'customText', 'emphasize'}
        for activity_dict in activities:
            if set(activity_dict.keys()).issubset(set_of_expected_keys) and 'activityId' in set_of_expected_keys:
                # Check whether the activityId is class `Activity` or UUID
                activity = activity_dict['activityId']
                if isinstance(activity, Activity):
                    activity_dict['activityId'] = activity.id
                elif isinstance(activity, text_type) and is_uuid(activity):
                    pass
                else:
                    raise IllegalArgumentError("When using the add_navigation_bar_widget, activityId must be an "
                                               "Activity or Activity id. Type is: {}".format(type(activity)))
                if 'customText' not in activity_dict.keys() or not activity_dict['customText']:
                    activity_dict['customText'] = str()
                if 'emphasize' not in activity_dict.keys():
                    activity_dict['emphasize'] = False

            else:
                raise IllegalArgumentError("Found unexpected key in activities. Only keys allowed are: {}".
                                           format(set_of_expected_keys))

        # Declare navigation bar widget config
        config = {
            'alignment': alignment,
            'xtype': ComponentXType.ACTIVITYNAVIGATIONBAR,
            'filter': {
                'activity_id': str(self.activity.id)
            },
            'taskButtons': activities
        }

        for activity_dict in activities:
            activity_id = activity_dict['activityId']
            activity_dict['name'] = self._client.activity(id=activity_id).name

        # Declare navigation bar widget meta
        meta = {
            'alignment': alignment,
            'activityId': str(self.activity.id),
            'taskButtons': activities
        }

        self._add_widget(dict(config=config, meta=meta, name=WidgetNames.TASKNAVIGATIONBARWIDGET))

from typing import Any, Optional, List, AnyStr, Dict

import requests
from jsonschema import validate

from pykechain.defaults import API_EXTRA_PARAMS
from pykechain.enums import WidgetTypes, Category
from pykechain.exceptions import APIError, IllegalArgumentError, NotFoundError, MultipleFoundError
from pykechain.models import BaseInScope
from pykechain.models.widgets.widget_schemas import widget_meta_schema


class Widget(BaseInScope):
    """A virtual object representing a KE-chain Widget.

    :cvar basestring id: UUID of the widget
    :cvar basestring title: Title of the widget
    :cvar basestring ref: Reference of the widget
    :cvar basestring widget_type: Type of the widget. Should be one of :class:`WidgetTypes`
    :cvar dict meta: Meta definition of the widget
    :cvar int order: Order of the widget in the list of widgets
    :cvar bool has_subwidgets: if the widgets contains any subwidgets. In case this widget being eg. a Multicolumn
    :cvar float progress: Progress of the widget
    """

    schema = widget_meta_schema

    def __init__(self, json: Dict, manager: 'WidgetsManager' = None, **kwargs) -> None:
        """Construct a Widget from a KE-chain 2 json response.

        :param json: the json response to construct the :class:`Part` from
        :type json: dict
        """
        # we need to run the init of 'Base' instead of 'Part' as we do not need the instantiation of properties
        super(Widget, self).__init__(json, **kwargs)
        del self.name

        self.manager = manager
        self.title = json.get('title')
        self.ref = json.get('ref')
        self.widget_type = json.get('widget_type')
        # set schema
        if self._client:
            self.schema = self._client.widget_schema(self.widget_type)

        self.meta = self.validate_meta(json.get('meta'))
        self.order = json.get('order')
        self._activity_id = json.get('activity_id')
        self._parent_id = json.get('parent_id')
        self.has_subwidgets = json.get('has_subwidgets')
        self._scope_id = json.get('scope_id')  # TODO duplicate with `scope_id` attribute
        self.progress = json.get('progress')

    def __repr__(self):  # pragma: no cover
        return "<pyke {} '{}' id {}>".format(self.__class__.__name__, self.widget_type, self.id[-8:])

    def activity(self):
        # type: () -> Activity2  # noqa: F821 to prevent circular imports
        """Activity associated to the widget.

        :return: The Activity
        :rtype: :class:`Activity2`
        """
        return self._client.activity(id=self._activity_id)

    def parent(self):
        # type: () -> Widget
        """Parent widget.

        :return: The parent of this widget.
        :rtype: :class:`Widget`
        """
        if not self._parent_id:
            raise NotFoundError('Widget has no parent widget (parent_id is null).')

        parent_widgets = self._client.widgets(pk=self._parent_id)
        if not parent_widgets:
            raise NotFoundError('No parent widget with uuid "{}" was found.'.format(self._parent_id))
        elif len(parent_widgets) > 1:
            raise MultipleFoundError('There are multiple widgets with uuid "{}".'.format(self._parent_id))
        else:
            return parent_widgets[0]

    def validate_meta(self, meta):
        # type: (dict) -> dict
        """Validate the meta and return the meta if validation is successfull.

        :param meta: meta of the widget to be validated.
        :type meta: dict
        :return meta: if the meta is validated correctly
        :raise: `ValidationError`
        """
        return validate(meta, self.schema) is None and meta

    @classmethod
    def create(cls, json: Dict, **kwargs) -> 'Widget':
        """Create a widget based on the json data.

        This method will attach the right class to a widget, enabling the use of type-specific methods.

        It does not create a widget object in KE-chain. But a pseudo :class:`Widget` object.

        :param json: the json from which the :class:`Widget` object to create
        :type json: dict
        :return: a :class:`Widget` object
        :rtype: :class:`Widget`
        """
        def _type_to_classname(widget_type):
            """
            Generate corresponding inner classname based on the widget type.

            :param widget_type: type of the widget (one of :class:`WidgetTypes`)
            :type widget_type: str
            :return: classname corresponding to the widget type
            :rtype: str
            """
            if widget_type is None:
                widget_type = WidgetTypes.UNDEFINED
            return "{}Widget".format(widget_type.title())

        widget_type = json.get('widget_type')

        # dispatcher to instantiate the right widget class based on the widget type
        # load all difference widget types from the pykechain.model.widgets module.
        import importlib
        all_widgets = importlib.import_module("pykechain.models.widgets")
        if hasattr(all_widgets, _type_to_classname(widget_type)):
            return getattr(all_widgets, _type_to_classname(widget_type))(json, client=kwargs.pop('client'), **kwargs)
        else:
            return getattr(all_widgets, _type_to_classname(WidgetTypes.UNDEFINED))(json, client=kwargs.pop('client'),
                                                                                   **kwargs)

        #
        # Searchers and retrievers
        #

    def parts(self, *args, **kwargs):
        # type: (*Any, **Any) -> Any
        """Retrieve parts belonging to this widget.

        Without any arguments it retrieves the Instances related to this widget only.

        This call only returns the configured properties in an widget. So properties that are not configured
        are not in the returned parts.

        See :class:`pykechain.Client.parts` for additional available parameters.

        """
        return self._client.parts(*args, widget=self.id, **kwargs)

    def associated_parts(self, *args, **kwargs):
        # type: (*Any, **Any) -> (Any, Any)
        """Retrieve models and instances belonging to this widget.

        This is a convenience method for the :func:`Widget.parts()` method, which is used to retrieve both the
        `Category.MODEL` as well as the `Category.INSTANCE` in a tuple.

        This call only returns the configured (associated) properties in a widget. So properties that are not
        configured (associated) are not in the returned parts.

        If you want to retrieve only the models associated to this task it is better to use:
            `Widget.parts(category=Category.MODEL)`.

        See :func:`pykechain.Client.parts` for additional available parameters.

        :returns: a tuple(models of :class:`PartSet`, instances of :class:`PartSet`)

        """
        return (
            self.parts(category=Category.MODEL, *args, **kwargs),
            self.parts(category=Category.INSTANCE, *args, **kwargs)
        )

    #
    # Write methods
    #
    def update_associations(self, readable_models=None, writable_models=None, **kwargs):
        # type: (Optional[List], Optional[List], **Any) -> None
        """
        Update associations on this widget.

        This is an absolute list of associations. If you provide No models, than the associations are cleared.

        Alternatively you may use `inputs` or `outputs` as a alias to `readable_models` and `writable_models`
        respectively.

        :param readable_models: list of property models (of :class:`Property` or property_ids (uuids) that has
                                read rights (alias = inputs)
        :type readable_models: List[Property] or List[UUID] or None
        :param writable_models: list of property models (of :class:`Property` or property_ids (uuids) that has
                                write rights (alias = outputs)
        :type writable_models: List[Property] or List[UUID] or None
        :param kwargs: additional keyword arguments to be passed into the API call as param.
        :return: None
        :raises APIError: when the associations could not be changed
        :raise IllegalArgumentError: when the list is not of the right type
        """
        self._client.update_widget_associations(widget=self, readable_models=readable_models,
                                                writable_models=writable_models, **kwargs)

    def edit(self, title=None, meta=None, **kwargs):
        # type: (Optional[AnyStr], Optional[Dict], **Any) -> None
        """Edit the details of a widget.

        :param title: (optional) title of the widget
        :type title: basestring or None
        :param meta: (optional) new Meta definition
        :type meta: dict or None
        :raises APIError: if the widget could not be updated.
        """
        update_dict = dict()

        if meta is not None:
            update_dict.update(dict(meta=meta))
        if title is not None:
            self.meta.update({'customTitle': title})
            update_dict.update(dict(meta=self.meta))
        if kwargs:
            update_dict.update(**kwargs)

        url = self._client._build_url('widget', widget_id=self.id)
        response = self._client._request('PUT', url, params=API_EXTRA_PARAMS['widgets'], json=update_dict)

        if response.status_code != requests.codes.ok:  # pragma: no cover
            raise APIError("Could not update Widget {}".format(self), response=response)

        self.refresh(json=response.json().get('results')[0])

    def delete(self) -> bool:
        """Delete the widget.

        :return: True when successful
        :rtype: bool
        :raises APIError: when unable to delete the activity
        """
        if self.manager:
            return self.manager.delete_widget(self)
        else:
            self._client.delete_widget(widget=self)

    def copy(self, target_activity, order=None):
        # type: (Activity2, Optional[int]) -> Widget
        """Copy the widget.

        :param target_activity: `Activity` object under which the desired `Widget` is copied
        :type target_activity: :class:`Activity`
        :param order: (optional) order in the activity of the widget.
        :type order: int or None
        :returns: copied :class:`Widget `
        :raises IllegalArgumentError: if target_activity is not :class:`Activity`

        >>> source_activity = project.activity('Source task')
        >>> target_activity = project.activity('Target task')
        >>> widget_manager = source_activity.widgets()
        >>> widget_to_copy = widget_manager[1]
        >>> widget_to_copy.copy(target_activity=target_activity, order=3)

        """
        from pykechain.models import Activity2
        if not isinstance(target_activity, Activity2):
            raise IllegalArgumentError("`target_activity` needs to be an activity, got '{}'".format(
                type(target_activity)))

        # Retrieve the widget manager of the target activity
        widget_manager = target_activity.widgets()

        # Get the writable and readable models of the original widget
        associated_part = self.parts(category=Category.MODEL)[0]
        readable_models = list()
        writable_models = list()
        for associated_property in associated_part.properties:
            if associated_property.output:
                writable_models.append(associated_property)
            else:
                readable_models.append(associated_property)

        # Create a perfect copy of the widget
        copied_widget = widget_manager.create_widget(meta=self.meta, widget_type=self.widget_type, title=self.title,
                                                     writable_models=writable_models, readable_models=readable_models,
                                                     order=order)

        return copied_widget

    def move(self, target_activity, order=None):
        # type: (Activity2, Optional[int]) -> Widget # noqa: F821
        """Move the widget.

        :param target_activity: `Activity` object under which the desired `Widget` is moved
        :type target_activity: :class:`Activity`
        :param order: (optional) order in the activity of the widget.
        :type order: int or None
        :returns: copied :class:`Widget `
        :raises IllegalArgumentError: if target_activity is not :class:`Activity`

        """
        moved_widget = self.copy(target_activity=target_activity, order=order)

        self.delete()

        return moved_widget

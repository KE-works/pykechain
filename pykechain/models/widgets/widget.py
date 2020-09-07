from typing import Any, Optional, List, AnyStr, Dict, Union, Text

import requests
from jsonschema import validate

from pykechain.defaults import API_EXTRA_PARAMS
from pykechain.enums import WidgetTypes, Category, WidgetTitleValue
from pykechain.exceptions import APIError, IllegalArgumentError, NotFoundError
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

        self.title = json.get("title")
        self.ref = json.get("ref")
        self.manager = manager

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

    @property
    def title_visible(self) -> Optional[Text]:
        """
        Return the title of the widget displayed in KE-chain.

        :return: title string
        :rtype str
        """
        show_title_value = self.meta.get("showTitleValue")
        if show_title_value == WidgetTitleValue.NO_TITLE:
            return None
        elif show_title_value == WidgetTitleValue.CUSTOM_TITLE:
            return self.meta.get("customTitle")

        elif show_title_value == WidgetTitleValue.DEFAULT:
            try:
                if self.widget_type == WidgetTypes.PROPERTYGRID:
                    return self._client.part(pk=self.meta.get("partInstanceId")).name
                elif self.widget_type in [WidgetTypes.FILTEREDGRID, WidgetTypes.SUPERGRID]:
                    return self._client.part(pk=self.meta.get("partModelId"), category=None).name
                elif self.widget_type in [WidgetTypes.SERVICE, WidgetTypes.NOTEBOOK]:
                    return self._client.service(pk=self.meta.get("serviceId")).name
                elif self.widget_type in [WidgetTypes.ATTACHMENTVIEWER, WidgetTypes.SIGNATURE]:
                    return self._client.property(pk=self.meta.get("propertyInstanceId"), category=None).name
                elif self.widget_type == WidgetTypes.CARD:
                    return self.scope.name
                else:
                    # TODO Weather, Scope and Task widgets display type in user's language: retrieve from locize API?
                    #  https://api.locize.app/b3df49f9-caf4-4282-9785-43113bff1ff7/latest/nl/common
                    return None

            except NotFoundError:  # pragma: no cover
                return None
        else:  # pragma: no cover
            return None

    def activity(self) -> 'Activity':
        """Activity associated to the widget.

        :return: The Activity
        :rtype: :class:`Activity`
        """
        return self._client.activity(id=self._activity_id)

    def parent(self) -> 'Widget':
        """Parent widget.

        :return: The parent of this widget.
        :rtype: :class:`Widget`
        """
        if not self._parent_id:
            raise NotFoundError('Widget has no parent widget (parent_id is null).')

        return self._client.widget(pk=self._parent_id)

    def validate_meta(self, meta: Dict) -> Dict:
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
        def _type_to_classname(type_widget: str):
            """
            Generate corresponding inner classname based on the widget type.

            :param type_widget: type of the widget (one of :class:`WidgetTypes`)
            :type type_widget: str
            :return: classname corresponding to the widget type
            :rtype: str
            """
            return "{}Widget".format(type_widget.title()) if type_widget else WidgetTypes.UNDEFINED

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

    def parts(self, *args, **kwargs) -> Any:
        """Retrieve parts belonging to this widget.

        Without any arguments it retrieves the Instances related to this widget only.

        This call only returns the configured properties in an widget. So properties that are not configured
        are not in the returned parts.

        See :class:`pykechain.Client.parts` for additional available parameters.

        """
        return self._client.parts(*args, widget=self.id, **kwargs)

    def associated_parts(self, *args, **kwargs) -> (Any, Any):
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
        models_and_instances = self._client.parts(*args, widget=self.id, category=None, **kwargs)

        models = [p for p in models_and_instances if p.category == Category.MODEL]
        instances = [p for p in models_and_instances if p.category == Category.INSTANCE]

        return models, instances

    #
    # Write methods
    #

    def update_associations(
            self,
            readable_models: Optional[List] = None,
            writable_models: Optional[List] = None,
            part_instance: Optional[Union['Part', Text]] = None,
            parent_part_instance: Optional[Union['Part', Text]] = None,
            **kwargs
    ) -> None:
        """
        Update associations on this widget.

        This is a patch to the list of associations: Existing associations are modified but not removed.

        Alternatively you may use `inputs` or `outputs` as a alias to `readable_models` and `writable_models`
        respectively.

        :param readable_models: list of property models (of :class:`Property` or property_ids (uuids) that has
                                read rights (alias = inputs)
        :type readable_models: List[Property] or List[UUID] or None
        :param writable_models: list of property models (of :class:`Property` or property_ids (uuids) that has
                                write rights (alias = outputs)
        :type writable_models: List[Property] or List[UUID] or None
        :param part_instance: Part object or UUID to be used as instance of the widget
        :type part_instance: Part or UUID
        :param parent_part_instance: Part object or UUID to be used as parent of the widget
        :type parent_part_instance: Part or UUID
        :param kwargs: additional keyword arguments to be passed into the API call as param.
        :return: None
        :raises APIError: when the associations could not be changed
        :raise IllegalArgumentError: when the list is not of the right type
        """
        self._client.update_widget_associations(
            widget=self,
            readable_models=readable_models,
            writable_models=writable_models,
            part_instance=part_instance,
            parent_part_instance=parent_part_instance,
            **kwargs
        )

    def set_associations(
            self,
            readable_models: Optional[List] = None,
            writable_models: Optional[List] = None,
            part_instance: Optional[Union['Part', Text]] = None,
            parent_part_instance: Optional[Union['Part', Text]] = None,
            **kwargs
    ) -> None:
        """
        Set associations on this widget.

        This is an absolute list of associations. If you provide No models, than the associations are cleared.

        Alternatively you may use `inputs` or `outputs` as a alias to `readable_models` and `writable_models`
        respectively.

        :param readable_models: list of property models (of :class:`Property` or property_ids (uuids) that has
                                read rights (alias = inputs)
        :type readable_models: List[Property] or List[UUID] or None
        :param writable_models: list of property models (of :class:`Property` or property_ids (uuids) that has
                                write rights (alias = outputs)
        :type writable_models: List[Property] or List[UUID] or None
        :param part_instance: Part object or UUID to be used as instance of the widget
        :type part_instance: Part or UUID
        :param parent_part_instance: Part object or UUID to be used as parent of the widget
        :type parent_part_instance: Part or UUID
        :param kwargs: additional keyword arguments to be passed into the API call as param.
        :return: None
        :raises APIError: when the associations could not be set
        :raise IllegalArgumentError: when the list is not of the right type
        """
        self._client.set_widget_associations(
            widget=self,
            readable_models=readable_models,
            writable_models=writable_models,
            part_instance=part_instance,
            parent_part_instance=parent_part_instance,
            **kwargs
        )

    def remove_associations(
            self,
            models: List[Union['Property', Text]],
            **kwargs
    ) -> None:
        """
        Remove associated properties from the widget.

        :param models: list of Properties or their uuids
        :return: None
        """
        self._client.remove_widget_associations(
            widget=self,
            models=models,
            **kwargs
        )

    def edit(
            self,
            title: Optional[AnyStr] = None,
            meta: Optional[Dict] = None,
            **kwargs
    ) -> None:
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
            self.meta.update({"customTitle": title, "showTitleValue": WidgetTitleValue.CUSTOM_TITLE})
            update_dict.update(dict(title=title, meta=self.meta))

        if kwargs:  # pragma: no cover
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

    def copy(self, target_activity: 'Activity', order: Optional[int] = None) -> 'Widget':
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
        from pykechain.models import Activity
        if not isinstance(target_activity, Activity):
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

    def move(self, target_activity: 'Activity', order: Optional[int] = None) -> 'Widget':
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

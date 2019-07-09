from typing import Any, Optional, List

import requests
from jsonschema import validate

from pykechain.enums import WidgetTypes
from pykechain.exceptions import APIError
from pykechain.models import Base
from pykechain.models.widgets.widget_schemas import widget_meta_schema


class Widget(Base):
    schema = widget_meta_schema

    def __init__(self, json, **kwargs):
        # type: (dict, **Any) -> None
        """Construct a part from a KE-chain 2 json response.

        :param json: the json response to construct the :class:`Part` from
        :type json: dict
        """
        # we need to run the init of 'Base' instead of 'Part' as we do not need the instantiation of properties
        super(Widget, self).__init__(json, **kwargs)
        del self.name

        self.title = json.get('title')
        self.widget_type = json.get('widget_type')
        self.meta = self.validate_meta(json.get('meta'))
        self.order = json.get('order')
        self._activity_id = json.get('activity_id')
        self._parent_id = json.get('parent_id')
        self.has_subwidgets = json.get('has_subwidgets')
        self._scope_id = json.get('scope_id')
        self.progress = json.get('progress')

    def __repr__(self):  # pragma: no cover
        return "<pyke {} '{}' id {}>".format(self.__class__.__name__, self.widget_type, self.id[-8:])

    def activity(self):
        return self._client.activity(id=self._activity_id)

    def parent(self):
        return self._client.widget(id=self._parent_id)

    def validate_meta(self, meta):
        # type: (dict) -> dict
        """Validate the meta and return the meta if validation is successfull.

        :param meta: meta of the widget to be validated.
        :type meta: dict
        :return meta: if the meta is validated correctly
        :raise: `ValidationError`
        """
        return validate(meta, self.schema) and meta

    @classmethod
    def create(cls, json, **kwargs):
        # type: (dict, **Any) -> Widget
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
        """Edit the details of a widget."""

        update_dict = {
            meta: meta,
            title: title
        }

        if kwargs:
            update_dict.update(**kwargs)

        url = self._client._build_url('widget', activity_id=self.id)

        response = self._client._request('PUT', url, json=update_dict)

        if response.status_code != requests.codes.ok:  # pragma: no cover
            raise APIError("Could not update Widget ({})".format(response))

        self.refresh(json=response.json().get('results')[0])

    def delete(self):
        """Delete the widget.

        :return: True when succesful
        :raises APIError: when unable to delete the activity
        """
        url = self._client._build_url('widget', widget_id=self.id)
        response = self._client._request('DELETE', url)

        if response.status_code != requests.codes.no_content:  # pragma: no cover
            raise APIError("Could not delete Widget ({})".format(response))

        return True

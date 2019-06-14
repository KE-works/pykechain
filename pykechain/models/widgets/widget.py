from pykechain.models import Base
from pykechain.utils import parse_datetime


class Widget(Base):

    def __init__(self, json, **kwargs):
        # type: (dict, **Any) -> None
        """Construct a part from a KE-chain 2 json response.

        :param json: the json response to construct the :class:`Part` from
        :type json: dict
        """
        # we need to run the init of 'Base' instead of 'Part' as we do not need the instantiation of properties
        super(Widget, self).__init__(json, **kwargs)
        del self.name

        self.title=json.get('title')
        self.widget_type = json.get('widget_type')
        self.meta = json.get('meta')
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

    @classmethod
    def create(cls, json, **kwargs):
        # type: (dict, **Any) -> Widget
        """Create a widget based on the json data.

        This method will attach the right class to a widget, enabling the use of type-specific methods.

        It does not create a widget object in KE-chain. But a pseudo :class:`Widget` object.

        :param json: the json from which the :class:`Widget` object to create
        :type json: dict
        :return: a :class:`Widget` object
        """
        def type_to_classname(widget_type):
            return "{}Widget".format(widget_type.title())

        widget_type = json.get('widget_type')

        import importlib

        all_widgets = importlib.import_module("pykechain.models.widgets")
        if hasattr(all_widgets, type_to_classname(widget_type)):
            return getattr(all_widgets, type_to_classname(widget_type))(json, **kwargs)
        else:
            return Widget(json, **kwargs)


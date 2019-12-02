from typing import Any, Dict

from pykechain.enums import URITarget, FontAwesomeMode
from pykechain.exceptions import IllegalArgumentError

allowed_attributes = ['displayName_nl', 'displayName_de', 'displayName_fr', 'displayName_it']


class SideBarButton(object):
    """
    Side-bar button class.

    Every custom button in the side-bar is maintained as an object of this class.
    The original KE-chain buttons for the project detail, tasks and work breakdown structure are not separate buttons.
    """

    def __init__(self, side_bar_manager, json=None, order=None, title=None, icon=None, uri=None,
                 uri_target=URITarget.INTERNAL, icon_mode=FontAwesomeMode.REGULAR, **kwargs):
        # type: (Any, Dict, int, str, str, str, URITarget, FontAwesomeMode, **Any) -> None
        """
        Create a side-bar button.

        :param side_bar_manager: Manager object to which the button is linked.
        :type side_bar_manager: SideBarManager
        :param json: the json response to construct the :class:`SideBarButton` from
        :type json: dict
        :param order: index of the button
        :type order: int
        :param title: visible label of the button
        :type title: str
        :param icon: FontAwesome icon of the button
        :type icon: str
        :param uri: Uniform Resource Identifier, the address of the linked page
        :type uri: str
        :param uri_target: type of URI, either internal or external
        :type uri_target: URITarget
        :param icon_mode: FontAwesome display mode of the icon
        :type icon_mode: FontAwesomeMode
        :returns None
        """
        super().__init__()

        if json is None:
            json = dict()

        title = title if title else json.get('displayName')
        order = order if order is not None else json.get('order')
        icon = icon if icon else json.get('displayIcon')
        uri = uri if uri else json.get('uri')
        uri_target = json.get('uriTarget', uri_target)
        icon_mode = json.get('displayIconMode', icon_mode)

        if not isinstance(order, int):
            raise IllegalArgumentError('order must be an integer, "{}" is not.'.format(order))
        if not isinstance(title, str):
            raise IllegalArgumentError('title must be a string, "{}" is not.'.format(title))
        if not isinstance(icon, str):
            raise IllegalArgumentError('icon must be a string, "{}" is not.'.format(icon))
        if not isinstance(uri, str):
            raise IllegalArgumentError('uri must be a string, "{}" is not.'.format(uri))
        if uri_target not in URITarget.values():
            raise IllegalArgumentError('uri_target must be a URITarget option, "{}" is not.'.format(uri_target))
        if icon_mode not in FontAwesomeMode.values():
            raise IllegalArgumentError('icon_mode must be a FontAwesomeMode option, "{}" is not.'.format(icon_mode))

        for key in kwargs.keys():
            if key not in allowed_attributes:
                raise IllegalArgumentError(
                    'Attribute "{}" is not supported in the configuration of a side-bar button.'.format(key))

        self._manager = side_bar_manager
        self.display_name = title  # type: str
        self.order = order  # type: int
        self.display_icon = icon  # type: str
        self.uri = uri  # type: str
        self.uri_target = uri_target  # type: URITarget
        self.display_icon_mode = icon_mode  # type: FontAwesomeMode

        self._other_attributes = kwargs

    def __repr__(self):
        return '{} {}: {}'.format(self.__class__.__name__, self.order, self.display_name)

    def refresh(self, json):
        """
        Refresh the object in-place using the provided json.

        :param json: the json response to construct the :class:`SideBarButton` from
        :type json: dict
        :return: None
        """
        self.__init__(side_bar_manager=self._manager, json=json)

    def edit(self, **kwargs):
        # type: (**Any) -> None
        """
        Edit the details of the button.

        :param kwargs:
        :return: None
        """
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)

        self._manager._update(buttons=self._manager._buttons)

    def delete(self):
        # type: () -> None
        """
        Delete the side-bar button from the side-bar.

        :return: None
        """
        self._manager.delete_button(key=self)

    def as_dict(self):
        # type: () -> Dict
        """
        Retrieve the configuration data, or `meta`, of the side-bar button.

        :return: dictionary of the configuration data
        :rtype dict
        """
        config = {
            "displayName": self.display_name,
            "displayIcon": self.display_icon,
            "uriTarget": self.uri_target,
            "uri": self.uri,
            "order": self.order,
            "displayIconMode": self.display_icon_mode,
        }
        config.update(self._other_attributes)

        return config

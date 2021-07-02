from typing import Dict, Optional

from pykechain.enums import FontAwesomeMode, URITarget
from pykechain.exceptions import IllegalArgumentError

allowed_attributes = ['displayName_nl', 'displayName_de', 'displayName_fr', 'displayName_it']


class SideBarButton:
    """
    Side-bar button class.

    Every custom button in the side-bar is maintained as an object of this class.
    The original KE-chain buttons for the project detail, tasks and work breakdown structure are not separate buttons.
    """

    def __init__(self,
                 side_bar_manager: 'SideBarManager',
                 json: Optional[Dict] = None,
                 order: Optional[int] = None,
                 title: Optional[str] = None,
                 icon: Optional[str] = None,
                 uri: Optional[str] = None,
                 uri_target: URITarget = URITarget.INTERNAL,
                 icon_mode: FontAwesomeMode = FontAwesomeMode.REGULAR,
                 **kwargs):
        """
        Create a side-bar button.

        :param side_bar_manager: Manager object to which the button is linked.
        :param json: the json response to construct the :class:`SideBarButton` from
        :param order: index of the button
        :param title: visible label of the button
        :param icon: FontAwesome icon of the button
        :param uri: Uniform Resource Identifier, the address of the linked page
        :param uri_target: type of URI, either internal or external
        :param icon_mode: FontAwesome display mode of the icon
        :returns None
        :raises IllegalArgumentError: When the provided Argument is not according to the type.
        """
        super().__init__()

        if json is None:
            json = {}

        title = title if title else json.get('displayName')
        order = order if order is not None else json.get('order')
        icon = icon if icon else json.get('displayIcon')
        uri = uri if uri else json.get('uri')
        uri_target = json.get('uriTarget', uri_target)
        icon_mode = json.get('displayIconMode', icon_mode)

        if not isinstance(order, int):
            raise IllegalArgumentError(f'order must be an integer, "{order}" is not.')
        if not isinstance(title, str):
            raise IllegalArgumentError(f'title must be a string, "{title}" is not.')
        if not isinstance(icon, str):
            raise IllegalArgumentError(f'icon must be a string, "{icon}" is not.')
        if not isinstance(uri, str):
            raise IllegalArgumentError(f'uri must be a string, "{uri}" is not.')
        if uri_target not in URITarget.values():
            raise IllegalArgumentError(f'uri_target must be a URITarget option, "{uri_target}" is not.')
        if icon_mode not in FontAwesomeMode.values():
            raise IllegalArgumentError(f'icon_mode must be a FontAwesomeMode option, "{icon_mode}" is not.')

        for key in kwargs.keys():
            if key not in allowed_attributes:
                raise IllegalArgumentError(
                    f'Attribute "{key}" is not supported in the configuration of a side-bar button.')

        self._manager: 'SideBarManager' = side_bar_manager
        self.display_name: str = title
        self.order: int = order
        self.display_icon: str = icon
        self.uri: str = uri
        self.uri_target: URITarget = uri_target
        self.display_icon_mode: FontAwesomeMode = icon_mode

        self._other_attributes = kwargs
        for key in allowed_attributes:
            if key in json:
                self._other_attributes[key] = json[key]

    def __repr__(self) -> str:
        return f'{self.__class__.__name__} {self.order}: {self.display_name}'

    def refresh(self, json: Optional[Dict] = None) -> None:
        """
        Refresh the object in-place using the provided json.

        :param json: the json response to construct the :class:`SideBarButton` from
        :return: None
        """
        self.__init__(side_bar_manager=self._manager, json=json or self.as_dict())

    def edit(self, **kwargs) -> None:
        """
        Edit the details of the button.

        :param kwargs:
        :return: None
        """
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
            elif key in allowed_attributes:
                self._other_attributes[key] = value

        self._manager._update()

    def delete(self) -> None:
        """
        Delete the side-bar button from the side-bar.

        :return: None
        """
        self._manager.delete_button(key=self)

    def as_dict(self) -> Dict:
        """
        Retrieve the configuration data, or `meta`, of the side-bar button.

        :return: dictionary of the configuration data
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

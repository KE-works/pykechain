from typing import Dict, Optional

from pykechain.enums import (
    FontAwesomeMode,
    SidebarAccessLevelOptions,
    SidebarItemAlignment,
    SidebarType,
    URITarget,
)
from pykechain.exceptions import IllegalArgumentError
from pykechain.models.sidebar.sidebar_base import SideBarItem


class SideBarButton(SideBarItem):
    """
    Side-bar button class.

    Every custom button in the side-bar is maintained as an object of this class.
    The original KE-chain buttons for the project detail, tasks and work breakdown
    structure are not separate buttons.

    :cvar allowed_attributes: allowed additional attributed provided as options alongside
        the specifically allowed ones.
    :cvar item_type: the item type of this class. Defaults to a BUTTON.
    """

    _allowed_attributes = [
        "displayName_nl",
        "displayName_en",
        "displayName_de",
        "displayName_fr",
        "displayName_it",
    ]
    _item_type = SidebarType.BUTTON

    def __init__(
        self,
        side_bar_manager: "SideBarManager",
        json: Optional[Dict] = None,
        title: Optional[str] = None,
        icon: Optional[str] = None,
        uri: Optional[str] = None,
        alignment: SidebarItemAlignment = SidebarItemAlignment.TOP,
        minimum_access_level: SidebarAccessLevelOptions = SidebarAccessLevelOptions.IS_MEMBER,
        uri_target: URITarget = URITarget.INTERNAL,
        icon_mode: FontAwesomeMode = FontAwesomeMode.REGULAR,
        **kwargs,
    ):
        """
        Create a side-bar button.

        :param side_bar_manager: Manager object to which the button is linked.
        :param json: the json response to construct the :class:`SideBarButton` from
        :param title: visible label of the button
        :param icon: FontAwesome icon of the button
        :param uri: Uniform Resource Identifier, the address of the linked page
        :param uri_target: type of URI, either internal or external
        :param alignment: alignment of the button top or bottom
        :param minimum_access_level: the minimum permission needed to see the button
        :param icon_mode: FontAwesome display mode of the icon
        :returns None
        :raises IllegalArgumentError: When the provided Argument is not according to the type.
        """
        super().__init__()

        if json is None:
            json = {}

        title = title if title else json.get("displayName")
        icon = icon if icon else json.get("displayIcon")
        uri = uri if uri else json.get("uri")
        uri_target = json.get("uriTarget", uri_target)
        icon_mode = json.get("displayIconMode", icon_mode)
        alignment = json.get("align", alignment)
        minimum_access_level = json.get("minimumAccessLevel", minimum_access_level)

        if not isinstance(title, str):
            raise IllegalArgumentError(f'title must be a string, "{title}" is not.')
        if not isinstance(icon, str):
            raise IllegalArgumentError(f'icon must be a string, "{icon}" is not.')
        if not isinstance(uri, str):
            raise IllegalArgumentError(f'uri must be a string, "{uri}" is not.')
        if uri_target not in URITarget.values():
            raise IllegalArgumentError(
                f'uri_target must be a URITarget option, "{uri_target}" is not.'
            )
        if icon_mode not in FontAwesomeMode.values():
            raise IllegalArgumentError(
                f'icon_mode must be a FontAwesomeMode option, "{icon_mode}" is not.'
            )

        for key in kwargs.keys():
            if key not in self._allowed_attributes:
                raise IllegalArgumentError(
                    f'Attribute "{key}" is not supported in the configuration of a side-bar'
                    " card."
                )

        self._manager: "SideBarManager" = side_bar_manager
        self.display_name: str = title
        self.display_icon: str = icon
        self.uri: str = uri
        self.uri_target: URITarget = uri_target
        self.display_icon_mode: FontAwesomeMode = icon_mode
        self.alignment: SidebarItemAlignment = alignment
        self.minimum_access_level: SidebarAccessLevelOptions = minimum_access_level

        self._other_attributes = kwargs
        for key in self._allowed_attributes:
            if key in json:
                self._other_attributes[key] = json[key]

    def as_dict(self) -> Dict:
        """
        Retrieve the configuration data, or `meta`, of the side-bar button.

        :return: dictionary of the configuration data
        :rtype dict
        """
        config = {
            "itemType": self._item_type,
            "displayName": self.display_name,
            "displayIcon": self.display_icon,
            "uriTarget": self.uri_target,
            "uri": self.uri,
            "displayIconMode": self.display_icon_mode,
            "align": self.alignment,
            "minimumAccessLevel": self.minimum_access_level,
        }
        config.update(self._other_attributes)
        config = {k: v for k, v in config.items() if v is not None}

        return config

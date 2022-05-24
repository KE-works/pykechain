from typing import Dict, Optional

from pykechain.enums import (
    Alignment,
    SidebarAccessLevelOptions,
    SidebarItemAlignment,
    SidebarType,
    URITarget,
)
from pykechain.exceptions import IllegalArgumentError
from pykechain.models.sidebar.sidebar_base import SideBarItem


class SideBarCard(SideBarItem):
    """
    Side-bar card class.

    Every side-bar can have one or more cards and is maintained as an object of this class.

    :cvar allowed_attributes: allowed additional attributed provided as options alongside
        the specifically allowed ones.
    :cvar item_type: the item type of this class. Defaults to a BUTTON.
    """

    _allowed_attributes = [
        "displayText_nl",
        "displayText_en",
        "displayText_de",
        "displayText_fr",
        "displayText_it",
        "actionButtonName_nl",
        "actionButtonName_en",
        "actionButtonName_de",
        "actionButtonName_fr",
        "actionButtonName_it",
    ]

    _item_type = SidebarType.CARD

    def __init__(
        self,
        side_bar_manager: "SideBarManager",
        json: Optional[Dict] = None,
        alignment: SidebarItemAlignment = SidebarItemAlignment.TOP,
        minimum_access_level: SidebarAccessLevelOptions = SidebarAccessLevelOptions.IS_MEMBER,
        maximum_access_level: SidebarAccessLevelOptions = SidebarAccessLevelOptions.IS_MANAGER,
        display_text: str = None,
        show_close_action: bool = True,
        show_background: bool = True,
        show_action_button: bool = False,
        action_button_name: Optional[str] = None,
        action_button_uri: Optional[str] = None,
        action_button_uri_target: Optional[str] = None,
        display_text_align: Optional[Alignment] = Alignment.CENTER,
        **kwargs: dict,
    ) -> None:
        """
        Create a side-bar card.

        :param side_bar_manager: Manager object to which the button is linked.
        :param json: the json response to construct the :class:`SideBarButton` from
        :param title: visible label of the button
        :param icon: FontAwesome icon of the button
        :param uri: Uniform Resource Identifier, the address of the linked page
        :param uri_target: type of URI, either internal or external
        :param alignment: alignment of the button top or bottom
        :param minimum_access_level: the minimum permission needed to see the button
        :param maximum_access_level: the maximum permission needed to see the button
        :param icon_mode: FontAwesome display mode of the icon
        :returns None
        :raises IllegalArgumentError: When the provided Argument is not according to the type.
        """
        super().__init__()

        if json is None:
            json = {}
        self._manager: "SideBarManager" = side_bar_manager
        self.align = json.get("align", alignment)
        self.minimum_access_level = json.get("minimumAccessLevel", minimum_access_level)
        self.maximum_access_level = json.get("maximumAccessLevel", maximum_access_level)

        self.display_text = json.get("displayText", display_text)
        self.display_text_align = json.get("displayTextAlign", display_text_align)
        self.show_close_action = json.get("showCloseaction", show_close_action)
        self.show_background = json.get("showBackground", show_background)
        self.show_action_button = json.get("showActionButton", show_action_button)
        self.action_button_name = json.get("actionButtonName", action_button_name)
        self.action_button_uri = json.get("actionButtonUri", action_button_uri)
        self.action_button_uri_target = json.get(
            "actionButtonUriTarget", action_button_uri_target
        )

        if (
            self.action_button_uri_target is not None
            and self.action_button_uri_target not in URITarget.values()
        ):
            raise IllegalArgumentError(
                f'uri_target must be a URITarget option, "{self.action_button_uri_target}" is not.'
            )
        if self.align not in SidebarItemAlignment.values():
            raise IllegalArgumentError(
                f"alignment must be a proper `SidebarButtonAlgment` type, '{self.align} is not.'"
            )

        for key in kwargs.keys():
            if key not in self._allowed_attributes:
                raise IllegalArgumentError(
                    f'Attribute "{key}" is not supported in the configuration of a side-bar'
                    " card."
                )

        self._other_attributes = kwargs
        for key in self._allowed_attributes:
            if key in json:
                self._other_attributes[key] = json[key]

    def as_dict(self) -> Dict:
        """
        Retrieve the configuration data, or `meta`, of the side-bar button.

        :return: dictionary of the configuration data

        Example
        -------
        ```{
            "itemType": "CARD",
            "order": 5,
            "align": "top",
            "showCloseAction": true,
            "showActionButton": true,
            "actionButtonUri": "https://asdasdas",
            "actionButtonUriTarget": "_new",
            "actionButtonName": "Discover more",
            "displayText": "This project ...",
            "displayText_nl": "Dit project ...",
            "displayTextAlign": "left",
            "showBackground": true,
            "minimumAccessLevel": "is_member",
            "maximumAccessLevel": "is_supervisor",
        }```

        """
        config = {
            "itemType": self._item_type,
            "displayText": self.display_text,
            "displayTextAlign": self.display_text_align,
            "align": self.align,
            "minimumAccessLevel": self.minimum_access_level,
            "maximumAccessLevel": self.maximum_access_level,
            "showBackground": self.show_background,
            "showCloseAction": self.show_close_action,
            "showActionButton": self.show_action_button,
            "actionButtonName": self.action_button_name,
            "actionButtonUri": self.action_button_uri,
            "actionButtonUriTarget": self.action_button_uri_target,
        }
        config.update(self._other_attributes)
        config = {k: v for k, v in config.items() if v is not None}

        return config

from typing import Dict, Optional

from pykechain.enums import SidebarType


class SideBarItem:
    """
    A base class for all various sidebar 'widgets'.

    :cvar allowed_attributes: allowed additional attributed provided as options alongside
        the specifically allowed ones.
    :cvar item_type: the item type of this class. Defaults to a BUTTON.
    """

    _allowed_attributes = []
    _item_type = SidebarType.BUTTON

    def __repr__(self) -> str:
        if hasattr(self, "title"):
            name = getattr(self, "title")
        elif hasattr(self, "display_text"):
            name = getattr(self, "display_text")
        else:
            name = "<no name>"
        return f"<pyke {self.__class__.__name__}: '{name}'>"

    def refresh(self, json: Optional[Dict] = None) -> None:
        """
        Refresh the object in-place using the provided json.

        :param json: the json response to construct the :class:`SideBarButton` from
        :type json: dict
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
            elif key in self._allowed_attributes:
                self._other_attributes[key] = value

        self._manager._update()

    def delete(self) -> None:
        """
        Delete the side-bar button from the side-bar.

        :return: None
        """
        self._manager.delete_button(key=self)

    def as_dict(self) -> Dict:
        """Represent the sidebar object as a dictionary."""
        raise NotImplementedError("The method `as_dict()` need to be implemented.")

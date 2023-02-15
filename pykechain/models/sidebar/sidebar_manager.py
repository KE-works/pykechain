from collections.abc import Iterable
from typing import Any, Dict, List, Optional

from pykechain.enums import (
    KEChainPageIcons,
    KEChainPageLabels,
    KEChainPages,
    SidebarType,
    SubprocessDisplayMode,
    URITarget,
)
from pykechain.exceptions import NotFoundError
from pykechain.models.input_checks import (
    check_enum,
    check_list_of_dicts,
    check_text,
    check_type,
    check_url,
)
from pykechain.models.sidebar.sidebar_base import SideBarItem
from pykechain.models.sidebar.sidebar_button import SideBarButton
from pykechain.models.sidebar.sidebar_card import SideBarCard
from pykechain.utils import find


class SideBarManager(Iterable):
    """
    Sidebar manager class.

    :ivar scope: Scope object for which the side-bar is managed.
    :ivar bulk_creation: boolean to create buttons in bulk, postponing updating of KE-chain until the manager is
                         deleted from memory (end of your function)
    """

    __existing_managers = (
        dict()
    )  # storage of manager objects to enforce 1 manager object per Scope

    def __new__(cls, scope: "Scope", *args, **kwargs):
        """Overwrite superclass method to enforce singleton manager per Scope object."""
        instance = super().__new__(cls)

        # Singleton manager per scope: this is required to support bulk_creation
        if scope.id in cls.__existing_managers:
            instance = cls.__existing_managers[scope.id]
        else:
            cls.__existing_managers[scope.id] = instance

        return instance

    def __init__(self, scope: "Scope", **kwargs):
        """
        Create a side-bar manager object for the Scope object.

        :param scope: Scope for which to create the side-bar manager.
        :param bulk_creation: flag whether to update once (True) or continuously (False, default)
        """
        super().__init__(**kwargs)

        from pykechain.models import Scope

        check_type(scope, Scope, "scope")

        self.scope: Scope = scope
        self._override: bool = scope.options.get("overrideSideBar", False)

        self._scope_uri = f"#/scopes/{self.scope.id}"
        self._perform_bulk_creation = False

        self._items: List[SideBarItem] = []

        # Load existing buttons from the scope
        for item_dict in scope.options.get("customNavigation", []):
            if item_dict.get("itemType", SidebarType.BUTTON) == SidebarType.BUTTON:
                self._items.append(SideBarButton(side_bar_manager=self, json=item_dict))
            elif item_dict.get("itemType") == SidebarType.CARD:
                self._items.append(SideBarCard(side_bar_manager=self, json=item_dict))

        self._iter = iter(self._items)

    def __repr__(self) -> str:  # pragma: no cover
        return f"<pyke {self.__class__.__name__}: {self.__len__()} items>"

    def __iter__(self):
        return self

    def __len__(self) -> int:
        return len(self._items)

    def __next__(self) -> SideBarItem:
        return next(self._iter)

    def __getitem__(self, key: Any) -> SideBarItem:

        found = None
        if isinstance(key, SideBarItem):
            found = find(self._items, lambda b: b == key)

        if isinstance(key, int):
            found = self._items[key]
        elif isinstance(key, str):
            found = find(self._items, lambda p: key == p.display_name)

        if found is not None:
            return found
        raise NotFoundError(f"Could not find button with index or name '{key}'")

    def __enter__(self):
        """
        Open context manager using the `with` keyword to postpone updates to KE-chain.

        >>> with scope.side_bar() as manager:
        >>>     button = manager.add_ke_chain_page(page_name=KEChainPages.EXPLORER)
        >>>     manager.insert(index=0, button=button)
        """
        self._perform_bulk_creation = True
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._perform_bulk_creation = False
        self._update()

    def refresh(self) -> None:
        """Reload the scope options from KE-chain to refresh the side-bar data."""
        self.scope.refresh()
        self.__init__(scope=self.scope)

    def remove(self, key: Any) -> None:
        """
        Remove a button from the side-bar.

        :param key: either a button, index, or name.
        :returns None
        """
        self.delete_button(key=key)

    def insert(self, index: int, button: SideBarItem) -> None:
        """
        Place a button at index `index` of the button-list.

        :param index: location index of the new button
        :param button: a side-bar button object
        """
        if button in self._items:
            self._items.remove(button)

        self._items.insert(check_type(index, int, "index"), button)

    def create_card(self, order: Optional[int] = None, *args, **kwargs) -> SideBarCard:
        """Create a side bar card.

        :param order: Optional input to specify where the button is injected in the list of items.
        :return: new side-bar card
        """
        if order is None:
            index = len(self._items)
        else:
            index = check_type(order, int, "order")

        card = SideBarCard(side_bar_manager=self, *args, **kwargs)
        # insert the button on a certain position in the list of items.
        self._items.insert(index, card)
        self._update()
        return card

    def create_button(
        self, order: Optional[int] = None, *args, **kwargs
    ) -> SideBarButton:
        """
        Create a side-bar button.

        :param order: Optional input to specify where the button is injected in the list of items.
        :return: new side-bar button
        """
        if order is None:
            index = len(self._items)
        else:
            index = check_type(order, int, "order")

        button = SideBarButton(side_bar_manager=self, *args, **kwargs)
        # insert the button on a certain position in the list of items.
        self._items.insert(index, button)
        self._update()
        return button

    def add_task_button(
        self,
        activity: "Activity",
        title: Optional[str] = None,
        task_display_mode: Optional[
            SubprocessDisplayMode
        ] = SubprocessDisplayMode.ACTIVITIES,
        *args,
        **kwargs,
    ) -> SideBarButton:
        """
        Add a side-bar button to a KE-chain activity.

        :param activity: Activity object
        :param title: Title of the side-bar button, defaults to the activity name
        :param task_display_mode: for sub-processes, vary the display mode in KE-chain
        :return: new side-bar button
        """
        from pykechain.models import Activity

        check_type(activity, Activity, "activity")
        check_enum(task_display_mode, SubprocessDisplayMode, "task_display_mode")
        title = check_text(title, "title") or activity.name

        uri = f"{self._scope_uri}/{task_display_mode}/{activity.id}"

        uri_target = (
            URITarget.INTERNAL
            if activity.scope_id == self.scope.id
            else URITarget.EXTERNAL
        )

        return self.create_button(
            uri=uri, uri_target=uri_target, title=title, *args, **kwargs
        )

    def add_ke_chain_page(
        self, page_name: KEChainPages, title: Optional[str] = None, *args, **kwargs
    ) -> SideBarButton:
        """
        Add a side-bar button to a built-in KE-chain page.

        :param page_name: name of the KE-chain page
        :param title: Title of the side-bar button, defaults to the page_name
        :return: new side-bar button
        """
        page_name = check_enum(page_name, KEChainPages, "page_name")
        title = check_text(title, "title") or KEChainPageLabels[page_name]
        icon = KEChainPageIcons[page_name]
        if "icon" in kwargs:
            icon = kwargs.pop("icon")

        uri = f"{self._scope_uri}/{page_name}"

        return self.create_button(
            uri=uri,
            uri_target=URITarget.INTERNAL,
            title=title,
            icon=icon,
            *args,
            **kwargs,
        )

    def add_external_button(
        self, url: str, title: str, *args, **kwargs
    ) -> SideBarButton:
        """
        Add a side-bar button to an external page defined by an URL.

        :param title: title of the button
        :param url: URL to an external page
        :return: new side-bar button
        """
        button = self.create_button(
            title=check_text(title, "title"),
            uri=check_url(url),
            uri_target=URITarget.EXTERNAL,
            *args,
            **kwargs,
        )
        return button

    def add_buttons(
        self, buttons: List[Dict], override_sidebar: bool
    ) -> List[SideBarItem]:
        """
        Create a list of buttons in bulk. Each button is defined by a dict, provided in a sorted list.

        :param buttons: list of dicts
        :param override_sidebar: whether to override the default sidebar menu items.
        :return: list of SideBarButton objects
        """
        check_list_of_dicts(buttons, "buttons")
        check_type(override_sidebar, bool, "override_sidebar")

        for index, button in enumerate(buttons):
            button = SideBarButton(side_bar_manager=self, json=button)

            self._items.append(button)

        self.override_sidebar = override_sidebar
        self._update()
        return self._items

    def delete_button(self, key: Any) -> None:
        """
        Similar to the `remove` method, deletes a button.

        :param key: either a button, index or name
        :return: None
        """
        item = self[key]
        self._items.remove(item)
        self._update()

    @property
    def override_sidebar(self) -> bool:
        """
        Flag to indicate whether the original KE-chain side-bar is still shown.

        :return: boolean, True if original side-bar is not visible
        """
        return self._override

    @override_sidebar.setter
    def override_sidebar(self, value: bool) -> None:
        """
        Flag to indicate whether the original KE-chain side-bar is still shown.

        :param value: new boolean value
        :return: None
        """
        check_type(value, bool, "override_sidebar")
        self._override = value
        self._update()

    def _update(self) -> None:
        """
        Update the side-bar using the scope.options attribute.

        :return: None
        """
        if self._perform_bulk_creation:
            # Update will proceed during deletion of the manager.
            return

        options = dict(self.scope.options)

        custom_navigation = list()
        for item in self._items:
            custom_navigation.append(item.as_dict())

        options.update(
            customNavigation=custom_navigation,
            overrideSideBar=self._override,
        )

        self.scope.options = options

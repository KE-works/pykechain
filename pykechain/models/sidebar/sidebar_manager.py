from collections.abc import Iterable
from typing import Any, Optional, Text, List, Dict

from pykechain.enums import URITarget, SubprocessDisplayMode, KEChainPages, KEChainPageLabels, KEChainPageIcons
from pykechain.exceptions import NotFoundError
from pykechain.models.input_checks import check_url, check_text, check_enum, check_list_of_dicts, check_type
from pykechain.models.sidebar.sidebar_button import SideBarButton
from pykechain.utils import find


class SideBarManager(Iterable):
    """
    Sidebar manager class.

    :ivar scope: Scope object for which the side-bar is managed.
    :type scope: Scope
    :ivar bulk_creation: boolean to create buttons in bulk, postponing updating of KE-chain until the manager is
                         deleted from memory (end of your function)
    :type bulk_creation: bool
    """

    __existing_managers = dict()  # storage of manager objects to enforce 1 manager object per Scope

    def __new__(cls, scope: 'Scope', *args, **kwargs):
        """Overwrite superclass method to enforce singleton manager per Scope object."""
        instance = super().__new__(cls)

        # Singleton manager per scope: this is required to support bulk_creation
        if scope.id in cls.__existing_managers:
            instance = cls.__existing_managers[scope.id]
        else:
            cls.__existing_managers[scope.id] = instance

        return instance

    def __init__(self, scope: 'Scope', **kwargs):
        """
        Create a side-bar manager object for the Scope object.

        :param scope: Scope for which to create the side-bar manager.
        :type scope: Scope
        :param bulk_creation: flag whether to update once (True) or continuously (False, default)
        :type bulk_creation: bool
        """
        super().__init__(**kwargs)

        from pykechain.models import Scope
        check_type(scope, Scope, 'scope')

        self.scope: Scope = scope
        self._override: bool = scope.options.get('overrideSideBar', False)

        self._scope_uri = "#/scopes/{}".format(self.scope.id)
        self._perform_bulk_creation = False

        self._buttons: List[SideBarButton] = []

        # Load existing buttons from the scope
        for button_dict in scope.options.get('customNavigation', []):
            self._buttons.append(SideBarButton(side_bar_manager=self, json=button_dict))

        self._iter = iter(self._buttons)

    def __repr__(self) -> Text:  # pragma: no cover
        return "<pyke {} object {} buttons>".format(self.__class__.__name__, self.__len__())

    def __iter__(self):
        return self

    def __len__(self) -> int:
        return len(self._buttons)

    def __next__(self) -> SideBarButton:
        # py3.4 and up style next
        return next(self._iter)

    def __getitem__(self, key: Any) -> SideBarButton:

        found = None
        if isinstance(key, SideBarButton):
            found = find(self._buttons, lambda b: b == key)

        if isinstance(key, int):
            found = self._buttons[key]
        elif isinstance(key, str):
            found = find(self._buttons, lambda p: key == p.display_name)

        if found is not None:
            return found
        raise NotFoundError("Could not find button with index or name '{}'".format(key))

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
        :type key: Any
        :returns None
        """
        self.delete_button(key=key)

    def insert(self, index: int, button: SideBarButton) -> None:
        """
        Place a button at index `index` of the button-list.

        :param index: location index of the new button
        :type index: int
        :param button: a side-bar button object
        :type button: SideBarButton
        """
        if button in self._buttons:
            self._buttons.remove(button)

        self._buttons.insert(check_type(index, int, 'index'), button)

    def create_button(self, order: Optional[int] = None, *args, **kwargs) -> SideBarButton:
        """
        Create a side-bar button.

        :param order: Optional input to specify the index of the new button.
        :type order: int
        :return: new side-bar button
        :rtype SideBarButton
        """
        if order is None:
            index = len(self._buttons)
        else:
            index = check_type(order, int, 'order')

        button = SideBarButton(side_bar_manager=self, order=index, *args, **kwargs)

        self._buttons.insert(index, button)

        self._update()

        return button

    def add_task_button(self,
                        activity: 'Activity',
                        title: Optional[Text] = None,
                        task_display_mode: Optional[SubprocessDisplayMode] = SubprocessDisplayMode.ACTIVITIES,
                        *args, **kwargs) -> SideBarButton:
        """
        Add a side-bar button to a KE-chain activity.

        :param activity: Activity object
        :type activity: Activity
        :param title: Title of the side-bar button, defaults to the activity name
        :type title: str
        :param task_display_mode: for sub-processes, vary the display mode in KE-chain
        :type task_display_mode: SubprocessDisplayMode
        :return: new side-bar button
        :rtype SideBarButton
        """
        from pykechain.models import Activity
        check_type(activity, Activity, 'activity')
        check_enum(task_display_mode, SubprocessDisplayMode, 'task_display_mode')
        title = check_text(title, 'title') or activity.name

        uri = '{}/{}/{}'.format(self._scope_uri, task_display_mode, activity.id)

        uri_target = URITarget.INTERNAL if activity.scope_id == self.scope.id else URITarget.EXTERNAL

        return self.create_button(uri=uri, uri_target=uri_target, title=title, *args, **kwargs)

    def add_ke_chain_page(self,
                          page_name: KEChainPages,
                          title: Optional[Text] = None,
                          *args, **kwargs) -> SideBarButton:
        """
        Add a side-bar button to a built-in KE-chain page.

        :param page_name: name of the KE-chain page
        :type page_name: KEChainPages
        :param title: Title of the side-bar button, defaults to the page_name
        :type title: str
        :return: new side-bar button
        :rtype SideBarButton
        """
        page_name = check_enum(page_name, KEChainPages, 'page_name')
        title = check_text(title, 'title') or KEChainPageLabels[page_name]
        icon = KEChainPageIcons[page_name]
        if 'icon' in kwargs:
            icon = kwargs.pop('icon')

        uri = '{}/{}'.format(self._scope_uri, page_name)

        return self.create_button(uri=uri, uri_target=URITarget.INTERNAL, title=title, icon=icon, *args, **kwargs)

    def add_external_button(self, url: Text, title: Text, *args, **kwargs) -> SideBarButton:
        """
        Add a side-bar button to an external page defined by an URL.

        :param title: title of the button
        :type title: str
        :param url: URL to an external page
        :type url: str
        :return: new side-bar button
        :rtype SideBarButton
        """
        button = self.create_button(
            title=check_text(title, 'title'),
            uri=check_url(url),
            uri_target=URITarget.EXTERNAL,
            *args, **kwargs
        )
        return button

    def add_buttons(self, buttons: List[Dict], override_sidebar: bool) -> List[SideBarButton]:
        """
        Create a list of buttons in bulk. Each button is defined by a dict, provided in a sorted list.

        :param buttons: list of dicts
        :type buttons: list
        :param override_sidebar: whether to override the default sidebar menu items.
        :type override_sidebar: bool
        :return: list of SideBarButton objects
        :rtype List[SideBarButton]
        """
        check_list_of_dicts(buttons, 'buttons')
        check_type(override_sidebar, bool, 'override_sidebar')

        for index, button in enumerate(buttons):
            button = SideBarButton(side_bar_manager=self, order=index, json=button)

            self._buttons.append(button)

        self.override_sidebar = override_sidebar
        self._update()

        return self._buttons

    def delete_button(self, key: Any) -> None:
        """
        Similar to the `remove` method, deletes a button.

        :param key: either a button, index or name
        :return: None
        """
        button = self[key]
        self._buttons.remove(button)
        self._update()

    @property
    def override_sidebar(self) -> bool:
        """
        Flag to indicate whether the original KE-chain side-bar is still shown.

        :return: boolean, True if original side-bar is not visible
        :rtype bool
        """
        return self._override

    @override_sidebar.setter
    def override_sidebar(self, value: bool) -> None:
        """
        Flag to indicate whether the original KE-chain side-bar is still shown.

        :param value: new boolean value
        :type value: bool
        :return: None
        """
        check_type(value, bool, 'override_sidebar')
        self._override = value
        self._update()

    def _update(self) -> None:
        """
        Update the side-bar using the scope.options attribute.

        :return: None
        :rtype None
        """
        if self._perform_bulk_creation:
            # Update will proceed during deletion of the manager.
            return

        options = dict(self.scope.options)

        custom_navigation = list()
        for button in self._buttons:
            custom_navigation.append(button.as_dict())

        options.update(
            customNavigation=custom_navigation,
            overrideSideBar=self._override,
        )

        self.scope.options = options

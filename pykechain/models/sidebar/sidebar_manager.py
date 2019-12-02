from typing import Sized, Any, Optional, Text, List, Dict

from six import string_types, text_type

from pykechain.enums import URITarget, SubprocessDisplayMode, KEChainPages, KEChainPageLabels
from pykechain.exceptions import NotFoundError, IllegalArgumentError
from pykechain.models.sidebar.sidebar_button import SideBarButton
from pykechain.utils import find


class SideBarManager(Sized):
    """
    Sidebar manager class.

    :ivar scope: Scope object for which the side-bar is managed.
    :type scope: Scope2
    :ivar bulk_creation: boolean to create buttons in bulk, postponing updating of KE-chain until the manager is
     deleted from memory (end of your function)
    :type bulk_creation: bool
    """

    __existing_managers = dict()  # storage of manager objects to enforce 1 manager object per Scope
    _bulk_creation = None  # ensure every instance has this attribute, regardless of the __init__ function.

    def __new__(cls, scope, *args, **kwargs):
        instance = super().__new__(cls)

        # Singleton manager per scope: this is required to support bulk_creation
        if scope.id in cls.__existing_managers:
            instance = cls.__existing_managers[scope.id]
        else:
            cls.__existing_managers[scope.id] = instance

        return instance

    def __init__(self, scope, bulk_creation=False, *args, **kwargs):
        # type: (Any, Optional[bool], *Any, **Any) -> None
        super().__init__(*args, **kwargs)

        from pykechain.models import Scope2
        if not isinstance(scope, Scope2):
            raise IllegalArgumentError('scope must be of class Scope2, "{}" is not.'.format(scope))

        if not isinstance(bulk_creation, bool):
            raise IllegalArgumentError('bulk_creation must be a boolean, "{}" is not.'.format(bulk_creation))

        self.scope = scope  # type: Scope2
        self._override = scope.options.get('overrideSidebar', False)  # type: bool
        self._scope_uri = "#/scopes/{}".format(self.scope.id)

        self._bulk_creation = bulk_creation  # type: bool

        # Load existing buttons from the scope
        self._buttons = list()  # type: list
        for button_dict in scope.options.get('customNavigation', list()):
            self._buttons.append(SideBarButton(side_bar_manager=self, json=button_dict))
        self._iter = iter(self._buttons)

    def __repr__(self):  # pragma: no cover
        return "<pyke {} object {} buttons>".format(self.__class__.__name__, self.__len__())

    def __iter__(self):
        return self

    def __len__(self):
        return len(self._buttons)

    def __next__(self):
        # py3.4 and up style next
        return next(self._iter)

    def __getitem__(self, key):

        found = None
        if isinstance(key, SideBarButton):
            found = find(self._buttons, lambda b: b == key)
        if isinstance(key, int):
            found = self._buttons[key]
        elif isinstance(key, (string_types, text_type)):
            found = find(self._buttons, lambda p: key == p.title or key == p.ref)

        if found is not None:
            return found
        raise NotFoundError("Could not find button with index or name '{}'".format(key))

    def __del__(self):
        """ Prior to deletion of the manager, an update to KE-chain is performed using the latest configuration. """
        if self._bulk_creation:
            # Set bulk creation to False in order for update to proceed correctly
            self._bulk_creation = False
            self._update(buttons=self._buttons, override_sidebar=self._override)

    def remove(self, key):
        self.delete_button(key=key)

    def insert(self, index, button):
        # type: (int, SideBarButton) -> None

        if not isinstance(index, int):
            raise IllegalArgumentError('Index "{}" is not an integer!'.format(index))

        self._buttons.insert(index, button)

    def create_button(self, order=None, *args, **kwargs):
        # type: (int, *Any, **Any) -> SideBarButton
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
            if not isinstance(order, int):
                raise IllegalArgumentError('order must be an integer, "{}" is not.'.format(order))
            index = order

        button = SideBarButton(side_bar_manager=self, order=index, *args, **kwargs)

        self._buttons.insert(index, button)

        self._update(buttons=self._buttons)

        return button

    def add_task_button(self, activity, title=None, task_display_mode=SubprocessDisplayMode.ACTIVITIES,
                        *args, **kwargs):
        # type: (Activity2, Optional[Text], Optional[SubprocessDisplayMode], *Any, **Any) -> SideBarButton
        """
        Add a side-bar button to a KE-chain activity.

        :param activity: Activity object
        :type activity: Activity2
        :param title: Title of the side-bar button, defaults to the activity name
        :type title: str
        :param task_display_mode: for sub-processes, vary the display mode in KE-chain
        :type task_display_mode: SubprocessDisplayMode
        :return: new side-bar button
        :rtype SideBarButton
        """
        from pykechain.models import Activity2

        if not isinstance(activity, Activity2):
            raise IllegalArgumentError('activity must be of class Activity2, "{}" is not.'.format(activity))

        if task_display_mode not in SubprocessDisplayMode.values():
            raise IllegalArgumentError('task_display_mode must be WorkBreakdownDisplayMode option, '
                                       '"{}" is not.'.format(task_display_mode))

        if title is not None:
            if not isinstance(title, str):
                raise IllegalArgumentError('title must be a string, "{}" is not.'.format(title))
        else:
            title = activity.name

        uri = '{}/{}/{}'.format(self._scope_uri, task_display_mode, activity.id)

        if activity.scope_id == self.scope.id:
            uri_target = URITarget.INTERNAL
        else:
            uri_target = URITarget.EXTERNAL

        return self.create_button(uri=uri, uri_target=uri_target, title=title, *args, **kwargs)

    def add_ke_chain_page(self, page_name, title=None, *args, **kwargs):
        # type: (KEChainPages, Optional[Text], *Any, **Any) -> SideBarButton
        """
        Add a side-bar button to a built-in KE-chain page.

        :param page_name: name of the KE-chain page
        :type page_name: KEChainPages
        :param title: Title of the side-bar button, defaults to the page_name
        :type title: str
        :return: new side-bar button
        :rtype SideBarButton
        """

        if page_name not in KEChainPages.values():
            raise IllegalArgumentError('page_name must be KEChainPages option, "{}" is not.'.format(page_name))

        if title is not None:
            if not isinstance(title, str):
                raise IllegalArgumentError('title must be a string, "{}" is not.'.format(title))
        else:
            title = KEChainPageLabels[page_name]

        uri = '{}/{}'.format(self._scope_uri, page_name)

        return self.create_button(uri=uri, uri_target=URITarget.INTERNAL, title=title, *args, **kwargs)

    def add_external_button(self, url, title, *args, **kwargs):
        # type: (str, Text, *Any, **Any) -> SideBarButton
        """
        Add a side-bar button to an external page defined by an URL.

        :param title: title of the button
        :type title: str
        :param url: URL to an external page
        :type url: str
        :return: new side-bar button
        :rtype SideBarButton
        """
        # TODO test url input for valid URL
        return self.create_button(title=title, uri=url, uri_target=URITarget.EXTERNAL, *args, **kwargs)

    def add_buttons(self, buttons, override_sidebar):
        # type: (List[Dict], bool) -> List[SideBarButton]
        """
        Create a list of buttons in bulk. Each button is defined by a dict, provided in a sorted list.

        :param buttons: list of dicts
        :type buttons: list
        :param override_sidebar: whether to override the default sidebar menu items.
        :type override_sidebar: bool
        :return: list of SideBarButton objects
        :rtype List[SideBarButton]
        """
        if not isinstance(buttons, list) or not all(isinstance(button, dict) for button in buttons):
            raise IllegalArgumentError('buttons must be a list of dictionaries, but received "{}"'.format(buttons))
        if not isinstance(override_sidebar, bool):
            raise IllegalArgumentError('override_sidebar must be a boolean, "{}" is not.'.format(override_sidebar))

        for index, button in enumerate(buttons):
            button = SideBarButton(side_bar_manager=self, order=index, json=button)

            self._buttons.append(button)

        self._update(buttons=self._buttons, override_sidebar=override_sidebar)

        return self._buttons

    def delete_button(self, key):
        # type: (Any) -> None
        button = self[key]
        self._buttons.remove(button)
        self._update(buttons=self._buttons)

    @property
    def override_sidebar(self):
        return self._override

    @override_sidebar.setter
    def override_sidebar(self, value):
        if not isinstance(value, bool):
            raise IllegalArgumentError('Override sidebar must be a boolean, "{}" is not.'.format(value))
        self._override = value
        self._update(override_sidebar=value)

    def _update(self, **kwargs):
        # type: (**Any) -> None
        """
        Update the side-bar using the scope.options attribute.

        :param kwargs: all keywords valid for scope.options
        :return: None
        :rtype None
        """

        if self._bulk_creation:
            # Update will proceed during deletion of the manager.
            return

        options = dict(self.scope.options)

        buttons = kwargs.pop('buttons', list())
        override = kwargs.pop('override_sidebar', self.scope.options.get('overrideSidebar'))

        custom_navigation = list()
        for button in buttons:
            custom_navigation.append(button.as_dict())

        options.update(
            customNavigation=custom_navigation,
            overrideSidebar=override,
            **kwargs
        )

        self.scope.options = options

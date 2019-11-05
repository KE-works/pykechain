from typing import Sized, Any, Optional, Text

from six import string_types, text_type

from pykechain.enums import URITarget, WorkBreakdownDisplayMode, KEChainPages, KEChainPageLabels
from pykechain.exceptions import NotFoundError, IllegalArgumentError
from pykechain.models.sidebar.sidebar_button import SideBarButton
from pykechain.utils import find


class SideBarManager(Sized):

    def __init__(self, scope, *args, **kwargs):
        # type: (Any, *Any, **Any) -> None
        super().__init__(*args, **kwargs)

        from pykechain.models import Scope2
        if not isinstance(scope, Scope2):
            raise IllegalArgumentError('scope must be of class Scope2, "{}" is not.'.format(scope))

        self._buttons = list()  # type: list
        self.scope = scope  # type: Scope2
        self._iter = iter(self._buttons)
        self._override = scope.options.get('overrideSidebar', False)  # type: bool

        self._scope_uri = "#/scopes/{}".format(self.scope.id)

        for button_dict in scope.options.get('customNavigation', list()):
            self.create_button(json=button_dict)

        # TODO if overrideSidebar is False, should the default buttons be loaded too (details, Tasks, WBS)?

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

    def add_task_button(self, activity, title=None, task_display_mode=WorkBreakdownDisplayMode.ACTIVITIES, *args, **kwargs):
        # type: (Activity2, Optional[Text], Optional[WorkBreakdownDisplayMode], *Any, **Any) -> SideBarButton
        """
        Add a side-bar button to a KE-chain activity.

        :param activity: Activity object
        :type activity: Activity2
        :param title: Title of the side-bar button, defaults to the activity name
        :type title: str
        :param task_display_mode: for sub-processes, vary the display mode in KE-chain
        :type task_display_mode: WorkBreakdownDisplayMode
        :return: new side-bar button
        :rtype SideBarButton
        """
        from pykechain.models import Activity2

        if not isinstance(activity, Activity2):
            raise IllegalArgumentError('activity must be of class Activity2, "{}" is not.'.format(activity))

        if task_display_mode not in KEChainPages.values:
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

        if page_name not in KEChainPages.values:
            raise IllegalArgumentError('page_name must be KEChainPages option, "{}" is not.'.format(page_name))

        if title is not None:
            if not isinstance(title, str):
                raise IllegalArgumentError('title must be a string, "{}" is not.'.format(title))
        else:
            title = KEChainPageLabels[page_name]

        uri = '{}/{}'.format(self._scope_uri, page_name)

        return self.create_button(uri=uri, uri_target=URITarget.INTERNAL, title=title, *args, **kwargs)

    def add_external_button(self, url, *args, **kwargs):
        # type: (str, *Any, **Any) -> SideBarButton
        """
        Add a side-bar button to an external page defined by an URL.
        :param url: URL to an external page
        :type url: str
        :return: new side-bar button
        :rtype SideBarButton
        """
        # TODO test url input for valid URL
        return self.create_button(uri=url, uri_target=URITarget.EXTERNAL, *args, **kwargs)

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

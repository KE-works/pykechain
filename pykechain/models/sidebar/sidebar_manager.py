from typing import Sized, Any, Optional

from six import string_types, text_type

from pykechain.enums import URITarget, WorkBreakdownDisplayMode, KEChainPages
from pykechain.exceptions import NotFoundError, IllegalArgumentError
from pykechain.models import Scope2, Activity2
from pykechain.models.sidebar.sidebar_button import SideBarButton
from pykechain.utils import find


class SideBarManager(Sized):

    def __init__(self, scope, override_sidebar=False, *args, **kwargs):
        # type: (Scope2, bool, *Any, **Any) -> None
        super().__init__(*args, **kwargs)

        buttons = scope.options.get('customNavigation', list())

        self.scope = scope  # type: Scope2
        self._buttons = list(buttons)  # type: list
        self._iter = iter(self._buttons)
        self._override = override_sidebar  # type: bool

        self._scope_uri = "#/scopes/{}/".format(self.scope.id)


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

    def pop(self, key):
        self.delete_button(key=key)

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

        self._update(customNavigation=self._buttons)
        return button

    def add_task_button(self, activity, task_display_mode=WorkBreakdownDisplayMode.ACTIVITIES, *args, **kwargs):
        # type: (Activity2, Optional[WorkBreakdownDisplayMode], *Any, **Any) -> SideBarButton
        """
        Add a side-bar button to a KE-chain activity.

        :param activity: Activity object
        :type activity: Activity2
        :param task_display_mode: for sub-processes, vary the display mode in KE-chain
        :type task_display_mode: WorkBreakdownDisplayMode
        :return: new side-bar button
        :rtype SideBarButton
        """

        if task_display_mode not in KEChainPages.values:
            raise IllegalArgumentError('task_display_mode must be WorkBreakdownDisplayMode option, '
                                       '"{}" is not.'.format(task_display_mode))

        uri = self._scope_uri + str(task_display_mode) + '/' + activity.id

        if activity.scope_id == self.scope.id:
            uri_target = URITarget.INTERNAL
        else:
            uri_target = URITarget.EXTERNAL

        return self.create_button(uri=uri, uri_target=uri_target, *args, **kwargs)

    def add_ke_chain_page(self, page_name, *args, **kwargs):
        # type: (KEChainPages, *Any, **Any) -> SideBarButton
        """
        Add a side-bar button to a built-in KE-chain page.

        :param page_name: name of the KE-chain page
        :type page_name: KEChainPages
        :return: new side-bar button
        :rtype SideBarButton
        """

        if page_name not in KEChainPages.values:
            raise IllegalArgumentError('page_name must be KEChainPages option, "{}" is not.'.format(page_name))

        uri = self._scope_uri + str(page_name)

        return self.create_button(uri=uri, uri_target=URITarget.INTERNAL, *args, **kwargs)

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
        button = self._buttons[key]
        self._buttons.remove(button)
        self._update(customNavigation=self._buttons)
        button.delete()

    @property
    def override_sidebar(self):
        return self._override

    @override_sidebar.setter
    def override_sidebar(self, value):
        if not isinstance(value, bool):
            raise IllegalArgumentError('Override sidebar must be a boolean, "{}" is not.'.format(value))
        self._override = value
        self._update(overrideSideBar=value)

    def _update(self, **kwargs):
        current_options = dict(self.scope.options)
        current_options.update(kwargs)
        self.scope.options = current_options

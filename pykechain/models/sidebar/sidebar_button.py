from typing import Text, Any, Optional

from pykechain.enums import URITarget, FontAwesomeMode, WorkBreakdownDisplayMode
from pykechain.exceptions import IllegalArgumentError


class SideBarButton(object):
    def __init__(self, side_bar_manager, order, title, icon, uri,
                 uri_target=URITarget.INTERNAL, icon_mode=FontAwesomeMode.REGULAR, **kwargs):
        # type: (Any, int, str, str, str, Optional[URITarget], Optional[FontAwesomeMode], **Any) -> None
        super().__init__()

        if uri_target not in URITarget.values():
            raise IllegalArgumentError('uri_target must be a URITarget option, "{}" is not.'.format(uri_target))
        if icon_mode not in FontAwesomeMode.values():
            raise IllegalArgumentError('icon_mode must be a FontAwesomeMode option, "{}" is not.'.format(icon_mode))

        self._manager = side_bar_manager
        self.display_name = title  # type: str
        self.order = order  # type: int
        self.display_icon = icon  # type: str
        self.uri = uri
        self.uri_target = uri_target
        self.display_icon_mode = icon_mode

        for key, value in kwargs.items():
            self.key = value

    def edit(self, title, **kwargs):
        # type: (Text, **Any) -> None
        self.display_name = title

    def delete(self):
        # type: () -> None
        self._manager.delete_button(self)

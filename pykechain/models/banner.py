import datetime
from typing import Text, Optional, Union

import requests

from pykechain.exceptions import APIError
from pykechain.models import Base
from pykechain.models.input_checks import check_text, check_datetime, check_type, check_url
from pykechain.utils import parse_datetime, Empty, clean_empty_values, empty


class Banner(Base):
    """
    A virtual object representing a KE-chain Banner.

    .. versionadded:: 3.6
    """

    def __init__(self, json, client):
        """Construct a banner from the provided json data."""
        super().__init__(json=json, client=client)

        self.text = json.get('text')
        self.icon = json.get('icon')
        self.is_active = json.get('is_active')
        self.active_from = parse_datetime(json.get('active_from'))
        self.active_until = parse_datetime(json.get('active_until'))
        self.url = json.get('url')

    def __repr__(self):  # pragma: no cover
        return "<pyke Banner '{}' id {}>".format(self.name, self.id[-8:])

    def edit(
        self,
        text: Optional[Union[Text, Empty]] = empty,
        icon: Optional[Union[Text, Empty]] = empty,
        active_from: Optional[Union[datetime.datetime, Empty]] = empty,
        active_until: Optional[Union[datetime.datetime, Empty]] = empty,
        is_active: Optional[Union[bool, Empty]] = empty,
        url: Optional[Union[Text, Empty]] = empty,
        **kwargs
    ) -> None:
        """
        Update the banner properties.

        Setting an input to None will clear out the value (exception being text, active_from, active_until and
        is_active).

        :param text: Text to display in the banner. May use HTML. Text cannot be cleared.
        :type text: basestring or Empty
        :param icon: Font-awesome icon to stylize the banner. Can be cleared.
        :type icon: basestring or None or Empty
        :param active_from: Datetime from when the banner will become active. Cannot be cleared.
        :type active_from: datetime.datetime or None or Empty
        :param active_until: Datetime from when the banner will no longer be active. Cannot be cleared.
        :type active_until: datetime.datetime or None or Empty
        :param is_active: Boolean whether to set the banner as active, defaults to False. Cannot be cleared.
        :type is_active: bool or Empty
        :param url: target for the "more info" button within the banner. Can be cleared.
        :param url: basestring or None or Empty
        :return: None

        Not mentioning an input parameter in the function will leave it unchanged. Setting a parameter as None will
        clear its value (when that is possible). The example below will clear the url and edit the text, but leave
        everything else unchanged.

        >>> banner.edit(text='New text here',url=None)

        """
        active = check_type(is_active, bool, 'is_active')
        update_dict = {
            'text': check_text(text, 'text'),
            'icon': check_text(icon, 'icon') or str(),
            'active_from': check_datetime(active_from, 'active_from') or check_datetime(
                self.active_from, 'active_from'),
            'active_until': check_datetime(active_until, 'active_until') or check_datetime(
                self.active_until, 'active_until'),
            'is_active': empty if active is None else active,
            'url': check_url(url) or str(),
        }

        if kwargs:  # pragma: no cover
            update_dict.update(kwargs)

        update_dict = clean_empty_values(update_dict=update_dict)

        if "text" not in update_dict or update_dict["text"] is None:
            update_dict["text"] = self.text

        url = self._client._build_url('banner', banner_id=self.id)

        response = self._client._request('PUT', url, json=update_dict)

        if response.status_code != requests.codes.ok:  # pragma: no cover
            raise APIError("Could not update Banner {}".format(self), response=response)

        self.refresh(json=response.json().get('results')[0])

    def delete(self) -> bool:
        """Delete this banner."""
        response = self._client._request('DELETE', self._client._build_url('banner', banner_id=self.id))

        if response.status_code != requests.codes.no_content:
            raise APIError("Could not delete Banner: {}".format(self), response=response)
        return True

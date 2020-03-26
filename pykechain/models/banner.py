import datetime
from typing import Text, Optional

import requests

from pykechain.exceptions import APIError, IllegalArgumentError
from pykechain.models import Base
from pykechain.utils import parse_datetime, is_url


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

    def edit(self,
             text: Optional[Text] = None,
             icon: Optional[Text] = None,
             active_from: Optional[datetime.datetime] = None,
             active_until: Optional[datetime.datetime] = None,
             is_active: Optional[bool] = None,
             url: Optional[Text] = None,
             ) -> None:
        """
        Update the banner properties.

        :param text: Text to display in the banner. May use HTML.
        :type text: str
        :param icon: Font-awesome icon to stylize the banner
        :type icon: str
        :param active_from: Datetime from when the banner will become active.
        :type active_from: datetime.datetime
        :param active_until: Datetime from when the banner will no longer be active.
        :type active_until: datetime.datetime
        :param is_active: Boolean whether to set the banner as active, defaults to False.
        :type is_active: bool
        :param url: target for the "more info" button within the banner.
        :param url: str
        :return: None
        """
        if text is not None and not isinstance(text, str):
            raise IllegalArgumentError('`text` must be a string, "{}" ({}) is not.'.format(text, type(text)))

        if icon is not None and not isinstance(icon, str):
            raise IllegalArgumentError('`icon` must be a string, "{}" ({}) is not.'.format(icon, type(icon)))

        if active_from is not None and not isinstance(active_from, datetime.datetime):
            raise IllegalArgumentError('`active_from` must be a datetime.datetime value, "{}" ({}) is not.'.format(
                active_from, type(active_from)))

        if active_until is not None and not isinstance(active_until, datetime.datetime):
            raise IllegalArgumentError('`active_until` must be a datetime.datetime value, "{}" ({}) is not.'.format(
                active_until, type(active_until)))

        if is_active is not None and not isinstance(is_active, bool):
            raise IllegalArgumentError('`is_active` must be a boolean, "{}" ({}) is not.'.format(is_active,
                                                                                                 type(is_active)))

        if url is not None and (not isinstance(url, str) or not is_url(url)):
            raise IllegalArgumentError('`url` must be a URL string, "{}" ({}) is not.'.format(url, type(url)))

        update_dict = {
            'text': text,
            'icon': icon,
            'active_from': active_from.isoformat(sep='T') if active_from else None,
            'active_until': active_until.isoformat(sep='T') if active_until else None,
            'is_active': is_active,
            'url': url,
        }

        url = self._client._build_url('banner', banner_id=self.id)

        response = self._client._request('PUT', url, json=update_dict)

        if response.status_code != requests.codes.ok:  # pragma: no cover
            raise APIError("Could not update Banner ({})".format(response))

        self.refresh(json=response.json().get('results')[0])

    def delete(self) -> bool:
        """Delete this banner."""
        response = self._client._request('DELETE', self._client._build_url('banner', banner_id=self.id))

        if response.status_code != requests.codes.no_content:
            raise APIError("Could not delete banner: {} with id {}".format(self.name, self.id))
        return True

import datetime
from typing import Text, Optional

import requests

from pykechain.exceptions import APIError
from pykechain.models import Base
from pykechain.models.input_checks import check_text, check_datetime, check_type, check_url
from pykechain.utils import parse_datetime


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
        update_dict = {
            'text': check_text(text, 'text') or self.text,
            'icon': check_text(icon, 'icon'),
            'active_from': check_datetime(active_from, 'active_from'),
            'active_until': check_datetime(active_until, 'active_until'),
            'is_active': check_type(is_active, bool, 'is_active'),
            'url': check_url(url),
        }

        # Remove None values
        items = [(key, value) for key, value in update_dict.items()]
        [update_dict.pop(key) for key, value in items if value is None]

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

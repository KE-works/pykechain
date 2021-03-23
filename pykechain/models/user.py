import datetime
from typing import Text

import pytz

from .base import Base
from ..enums import LanguageCodes


class User(Base):
    """A virtual object representing a KE-chain user.

    :ivar username: username of the user
    :type username: str
    :ivar name: username of the user (compatibility)
    :type name: str
    :ivar id: userid of the user
    :type id: int
    :ivar timezone: timezone of the User (defaults to <UTC>)
    :type timezone: timezone object
    :ivar language: language of the User (defaults to 'en')
    :type language: str
    :ivar email: email of the User (defaults to '')
    :type email: str
    """

    def __init__(self, json, **kwargs):
        """Construct a user from provided json data."""
        super(User, self).__init__(json, **kwargs)

        self.username = self._json_data.get('username', '')
        self.id = self._json_data.get('pk', '')

    def __repr__(self):  # pragma: no cover
        return "<pyke {} '{}' id {}>".format(self.__class__.__name__, self.username, self.id)

    @property
    def default_name(self) -> Text:
        """
        Get default name, prioritizing the user name over the KE-chain name.

        :return: Name
        :rtype str
        """
        return self.username if self.username else self.name

    @property
    def timezone(self) -> pytz.BaseTzInfo:
        """
        Timezone of the user.

        Defaults to timezone UTC.
        With return a pytz timezone eg. 'Europe/Amsterdam'

        :return: timezone object (compatible with datetime)
        :rtype: TzInfo
        """
        return pytz.timezone(zone=self._json_data.get('timezone', 'UTC'))

    @property
    def language(self) -> Text:
        """
        Language code of the user.

        Defaults to English ('en") when no language code is configured.

        :return: language code string
        :rtype: basestring
        """
        return self._json_data.get('language_code', LanguageCodes.ENGLISH)

    @property
    def email(self) -> Text:
        """
        Email of the user.

        :return: email address, default is empty string.
        :rtype: basestring
        """
        return self._json_data.get('email', '')

    def now_in_my_timezone(self) -> datetime.datetime:
        """
        Get current time in the timezone of the User.

        Defaults to timezone GMT+1 (Europe/Amsterdam).

        :return: Current datetime
        :rtype datetime.datetime
        """
        timezone_definition = self._json_data['timezone']
        if timezone_definition:
            timezone = pytz.timezone(timezone_definition)
        else:
            # if there is no timezone set then the Europe/Amsterdam timezone
            timezone = pytz.timezone('Europe/Amsterdam')

        # Default is utc timezone
        utc_time = datetime.datetime.now(tz=pytz.utc)

        # Convert to local timezone
        local_time = utc_time.astimezone(timezone)

        return local_time

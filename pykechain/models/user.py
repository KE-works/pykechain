import pytz

from .base import Base


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
    def timezone(self):
        """
        Timezone of the user.

        Defaults to timezone UTC.
        With return a pytz timezone eg. 'Europe/Amsterdam'

        :return: timezone object (compatible with datetime)
        :rtype: TzInfo
        """
        return pytz.timezone(zone=self._json_data.get('timezone', 'UTC'))

    @property
    def language(self):
        """
        Language code of the user.

        Defaults to English ('en") when no language code is configured.

        :return: language code string
        :rtype: basestring
        """
        return self._json_data.get('language_code', 'en')

    @property
    def email(self):
        """
        Email of the user.

        :return: email address, default is empty string.
        :rtype: basestring
        """
        return self._json_data.get('email', '')

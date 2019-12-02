import datetime
import warnings

from typing import Union, Text

from pykechain.exceptions import IllegalArgumentError
from pykechain.models import Property2
from pykechain.utils import parse_datetime


class DatetimeProperty2(Property2):
    """A virtual object representing a KE-chain reference property."""

    def __index__(self, json, **kwargs):
        super(DatetimeProperty2, self).__init__(json, **kwargs)

    @property
    def value(self):
        """Retrieve the data value of a property.

        Setting this value will immediately update the property in KE-chain.

        :returns: the value
        """
        return self._value

    @value.setter
    def value(self, value):
        if value is None:
            self._put_value(None)
        elif isinstance(value, datetime.datetime):
            if not value.tzinfo:
                warnings.warn("The value '{}' is naive and not timezone aware, use pytz.timezone info. "
                              "This date is interpreted as UTC time.".format(value.isoformat(sep=' ')))

            self._put_value(value.isoformat(sep='T'))
        else:
            raise IllegalArgumentError('value should be a datetime.datetime() object')

    def to_datetime(self):
        # type: () -> Union[type(None), datetime.datetime]
        """Retrieve the data value of a property.

        Setting this value will immediately update the property in KE-chain.

        :returns: the value
        """
        return parse_datetime(self._value)

    @staticmethod
    def to_iso_format(date_time):
        # type: (datetime.datetime) -> Text
        """Convert a datetime object to isoformat."""
        return date_time.isoformat()

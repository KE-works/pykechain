import datetime
from typing import Union, Text
from pykechain.exceptions import IllegalArgumentError, _DeprecationMixin
from pykechain.models import Property2
from pykechain.models.input_checks import check_datetime
from pykechain.utils import parse_datetime


class DatetimeProperty(Property2):
    """A virtual object representing a KE-chain reference property."""

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
            self._put_value(check_datetime(dt=value, key='value'))
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


class DatetimeProperty2(DatetimeProperty, _DeprecationMixin):
    """A virtual object representing a KE-chain reference property."""

    pass

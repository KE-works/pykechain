import datetime
from typing import Union, Text
from pykechain.exceptions import IllegalArgumentError
from pykechain.models import Property2
from pykechain.models.input_checks import check_datetime
from pykechain.utils import parse_datetime


class DatetimeProperty2(Property2):
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

    def serialize_value(self, value) -> str:
        """
        Serialize the value to be set on the property by checking for datetime objects.

        :param value: non-serialized value
        :type value: Any
        :return: serialized value
        """
        if isinstance(value, datetime.datetime):
            value = self.to_iso_format(value)
        return value

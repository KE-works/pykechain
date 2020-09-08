import datetime
from typing import Union, Text
from pykechain.models import Property
from pykechain.models.property2_datetime import DatetimeProperty2
from pykechain.models.input_checks import check_datetime
from pykechain.utils import parse_datetime


class DatetimeProperty(Property, DatetimeProperty2):
    """A virtual object representing a KE-chain datetime property."""

    @property
    def value(self):
        """Retrieve the data value of a property.

        Setting this value will immediately update the property in KE-chain.

        :returns: the value
        """
        return self._value

    @value.setter
    def value(self, value):
        value = check_datetime(dt=value, key='value')

        value = self.serialize_value(value)
        if self.use_bulk_update:
            self._pend_update(dict(value=value))
            self._value = value
        else:
            self._put_value(value)

    def to_datetime(self) -> Union[type(None), datetime.datetime]:
        """Retrieve the datetime as a datetime.datetime value.

        :returns: the value
        """
        return parse_datetime(self._value)

    @staticmethod
    def to_iso_format(date_time: datetime.datetime) -> Text:
        """Convert a datetime object to isoformat."""
        return date_time.isoformat()

    def serialize_value(self, value) -> Text:
        """
        Serialize the value to be set on the property by checking for datetime objects.

        :param value: non-serialized value
        :type value: Any
        :return: serialized value
        """
        if isinstance(value, datetime.datetime):
            value = self.to_iso_format(value)
        return value

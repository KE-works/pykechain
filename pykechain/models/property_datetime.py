import datetime
from typing import Union

from pykechain.models import Property
from pykechain.models.input_checks import check_datetime
from pykechain.utils import parse_datetime


class DatetimeProperty(Property):
    """A virtual object representing a KE-chain datetime property."""

    def to_datetime(self) -> Union[type(None), datetime.datetime]:
        """Retrieve the datetime as a datetime.datetime value.

        :returns: the value
        """
        return parse_datetime(self._value)

    @staticmethod
    def to_iso_format(date_time: datetime.datetime) -> str:
        """Convert a datetime object to isoformat."""
        return date_time.isoformat()

    def serialize_value(self, value) -> str:
        """
        Serialize the value to be set on the property by checking for formatted strings or datetime objects.

        :param value: non-serialized value
        :type value: Any
        :return: serialized value
        """
        return check_datetime(dt=value, key="value")

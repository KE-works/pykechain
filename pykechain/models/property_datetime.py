import datetime
import warnings

from pykechain.exceptions import IllegalArgumentError
from pykechain.models.property import Property
from pykechain.utils import parse_datetime


class DatetimeProperty(Property):  # pragma: no cover
    """A virtual object representing a KE-chain reference property."""

    def __index__(self, json, **kwargs):
        super(DatetimeProperty, self).__init__(json, **kwargs)

    @property
    def value(self):
        """Retrieve the data value of a property.

        Setting this value will immediately update the property in KE-chain.

        :returns: the value
        """
        return self._value

    @value.setter
    def value(self, value):
        if isinstance(value, datetime.datetime):
            if not value.tzinfo:
                warnings.warn("The value '{}' is naive and not timezone aware, use pytz.timezone info. "
                              "This date is interpreted as UTC time.".format(value.isoformat(sep=' ')))

            self._put_value(value.isoformat(sep='T'))
        else:
            raise IllegalArgumentError('value should be a datetime.datetime() object')

    def to_datetime(self):
        """Retrieve the data value of a property.

        Setting this value will immediately update the property in KE-chain.

        :returns: the value
        """
        return parse_datetime(self._value)

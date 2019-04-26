import datetime
import warnings

from pykechain.exceptions import IllegalArgumentError
from pykechain.models.property import Property
from pykechain.utils import parse_datetime


class DatetimeProperty(Property):
    """A virtual object representing a KE-chain reference property."""

    def as_datetime(self):
        """
        Transmogrify the value as a datetime object instead of a string.

        :return:
        """
        return parse_datetime(self.value)

    def to_value(self, obj):
        """
        Transmogrify the datetime object to a isostring for storage in the value.

        Will update the value and store it in the backend. Will make a backend call for it.

        :param datetime_object: datetime object can be provided as value setting.
        :type datetime_object: datetime
        :return:
        """
        if isinstance(obj, datetime.datetime):
            if not obj.tzinfo:
                warnings.warn("The value '{}' is naive and not timezone aware, use pytz.timezone info. "
                              "This date is interpreted as UTC time.".format(obj.isoformat(sep=' ')))

            self._put_value(obj.isoformat(sep='T'))
        else:
            raise IllegalArgumentError('Start date should be a datetime.datetime() object')

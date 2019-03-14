from pykechain.models.property import Property


class DatetimeProperty(Property):
    """A virtual object representing a KE-chain reference property."""

    def as_datetime(self):
        """
        Transmogrify the value as a datetime object instead of a string

        :return:
        """
        pass

    def to_value(self, datetime_object):
        """
        Transmogrify the datetime object to a isostring for storage in the value.

        Will update the value and store it in the backend. Will make a backend call for it.

        :param datetime_object: datetime object can be provided as value setting.
        :type datetime_object: datetime
        :return:
        """
        pass

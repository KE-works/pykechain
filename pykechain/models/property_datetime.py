from pykechain.models.property import Property


class DatetimeProperty(Property):
    """A virtual object representing a KE-chain reference property."""

    def as_datetime(self):
        """
        Transmogrify the value as a datetime object instead of a string

        :return:
        """
        pass

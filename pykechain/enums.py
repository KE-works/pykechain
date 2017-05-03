class Enum(object):
    """Custom enumeration class to support class attributes as options.

    Example
    -------

    >>> class Toppings(Enum):
    ...    CHEESE = "Cheese"
    ...    SALAMI = "Salami"
    >>> topping_choice = Toppings.CHEESE
    """

    @classmethod
    def options(cls):
        """Provide a sorted list of options."""
        return sorted((value, name) for (name, value) in cls.__dict__.items() if not name.startswith('__'))

    @classmethod
    def values(cls):
        """Provide a (sorted) list of values."""
        return [value for (name, value) in cls.options()]


class Multiplicity(Enum):
    """The various multiplicities that are accepted by KE-chain."""

    ZERO_ONE = "ZERO_ONE"
    ONE = "ONE"
    ZERO_MANY = "ZERO_MANY"
    ONE_MANY = "ONE_MANY"
    # M_N = "M_N"  # not implemented


class Category(Enum):
    """The various categories of Parts that are accepted by KE-chain."""

    INSTANCE = "INSTANCE"
    MODEL = "MODEL"


class PropertyType(Enum):
    """The various property types that are accepted by KE-chain."""

    FLOAT_VALUE = "FLOAT_VALUE"
    INT_VALUE = "INT_VALUE"
    TEXT_VALUE = "TEXT_VALUE"
    LINK_VALUE = "LINK_VALUE"
    REFERENCE_VALUE = "REFERENCE_VALUE"
    DATETIME_VALUE = "DATETIME_VALUE"
    BOOLEAN_VALUE = "BOOLEAN_VALUE"
    CHAR_VALUE = "CHAR_VALUE"
    ATTACHMENT_VALUE = "ATTACHMENT_VALUE"

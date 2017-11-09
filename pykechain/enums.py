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
        return [value for (value, name) in cls.options()]


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


class Classification(Enum):
    """The various classification of Parts that are accepted by KE-chain."""

    PRODUCT = "PRODUCT"
    CATALOG = "CATALOG"


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


class ActivityType(Enum):
    """The various Activity types that are accepted by KE-chain."""

    USERTASK = "UserTask"
    SERVICETASK = "ServiceTask"  # RND code only
    SUBPROCESS = "Subprocess"


class ComponentXType(Enum):
    """The various inspectortypes supported in the customized task in KE-chain."""

    PANEL = "panel"
    TOOLBAR = "toolbar"
    PROPERTYGRID = "propertyGrid"
    SUPERGRID = "superGrid"
    PAGINATEDSUPERGRID = "paginatedSuperGrid"
    FILTEREDGRID = "filteredGrid"
    DISPLAYFIELD = "displayfield"


class ActivityStatus(Enum):
    """The various Activity statuses that are accepted by KE-chain."""

    OPEN = 'OPEN'
    COMPLETED = 'COMPLETED'


class ScopeStatus(Enum):
    """The various status of a scope."""

    ACTIVE = 'ACTIVE'
    CLOSED = 'CLOSED'
    TEMPLATE = 'TEMPLATE'


class ServiceType(Enum):
    """The file types of sim script."""

    PYTHON_SCRIPT = 'PYTHON SCRIPT'
    NOTEBOOK = 'NOTEBOOK'


class ServiceEnvironmentVersion(Enum):
    """The acceptable versions of python where services run on."""

    PYTHON_2_7 = '2.7'
    PYTHON_3_5 = '3.5'
    PYTHON_3_5_NOTEBOOKS = '3.5_notebook'


class ServiceExecutionStatus(Enum):
    """The acceptable states of a running service."""

    LOADING = 'LOADING'
    RUNNING = 'RUNNING'
    COMPLETED = 'COMPLETED'
    FAILED = 'FAILED'
    TERMINATING = 'TERMINATING'
    TERMINATED = 'TERMINATED'


class KechainEnv(Enum):
    """Environment variables that can be set for pykechain."""

    KECHAIN_FORCE_ENV_USE = 'KECHAIN_FORCE_ENV_USE'
    KECHAIN_URL = 'KECHAIN_URL'
    KECHAIN_TOKEN = 'KECHAIN_TOKEN'
    KECHAIN_USERNAME = 'KECHAIN_USERNAME'
    KECHAIN_PASSWORD = 'KECHAIN_PASSWORD'
    KECHAIN_SCOPE = 'KECHAIN_SCOPE'
    KECHAIN_SCOPE_ID = 'KECHAIN_SCOPE_ID'
    KECHAIN_SCOPE_STATUS = 'KECHAIN_SCOPE_STATUS'

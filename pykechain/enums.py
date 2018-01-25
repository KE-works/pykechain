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
    """The various multiplicities that are accepted by KE-chain.

    :cvar ZERO_ONE: Multiplicity 0 to 1
    :cvar ONE: Multiplicity 1
    :cvar ZERO_MANY: Multiplicity 0 to infinity
    :cvar ONE_MANY: Multiplicity 1 to infinity
    """

    ZERO_ONE = "ZERO_ONE"
    ONE = "ONE"
    ZERO_MANY = "ZERO_MANY"
    ONE_MANY = "ONE_MANY"
    # M_N = "M_N"  # not implemented


class Category(Enum):
    """The various categories of Parts that are accepted by KE-chain.

    :cvar INSTANCE: Category of Instance
    :cvar MODEL: Category of Model
    """

    INSTANCE = "INSTANCE"
    MODEL = "MODEL"


class Classification(Enum):
    """The various classification of Parts that are accepted by KE-chain.

    :cvar PRODUCT: Classification of the part object is Product
    :cvar CATALOG: Classification of the part object is a CATALOG
    """

    PRODUCT = "PRODUCT"
    CATALOG = "CATALOG"


class PropertyType(Enum):
    """The various property types that are accepted by KE-chain.

    :cvar FLOAT_VALUE: floating point number property (with digits)
    :cvar INT_VALUE: integer property (whole number)
    :cvar TEXT_VALUE: text property (long text, may span multiple lines)
    :cvar LINK_VALUE: url property
    :cvar REFERENCE_VALUE: reference property, a UUID value referring to other parts
    :cvar DATETIME_VALUE: a datetime value property
    :cvar BOOLEAN_VALUE: a boolean value property (True/False)
    :cvar CHAR_VALUE: a charfield property (single line text)
    :cvar ATTACHMENT_VALUE: an attachment property

    .. versionadded:: 1.14

    :cvar SINGLE_SELECT_VALUE: single select list property (choose from a list)
    :cvar REFERENCES_VALUE: a multi reference property, a UUID value referring to other parts

    """

    FLOAT_VALUE = "FLOAT_VALUE"
    INT_VALUE = "INT_VALUE"
    TEXT_VALUE = "TEXT_VALUE"
    LINK_VALUE = "LINK_VALUE"
    SINGLE_SELECT_VALUE = 'SINGLE_SELECT_VALUE'
    REFERENCE_VALUE = "REFERENCE_VALUE"
    REFERENCES_VALUE = "REFERENCES_VALUE"
    DATETIME_VALUE = "DATETIME_VALUE"
    BOOLEAN_VALUE = "BOOLEAN_VALUE"
    CHAR_VALUE = "CHAR_VALUE"
    ATTACHMENT_VALUE = "ATTACHMENT_VALUE"


class ActivityType(Enum):
    """The various Activity types that are accepted by KE-chain.

    :cvar USERTASK: a normal usertask
    :cvar SUBPROCESS: a subprocess (container) containing other tasks
    :cvar SERVICETASK: a service taks (this concept is only availabe in RND KE-chain and will be deprecated)
    """

    USERTASK = "UserTask"
    SERVICETASK = "ServiceTask"  # RND code only
    SUBPROCESS = "Subprocess"


class ComponentXType(Enum):
    """The various inspectortypes supported in the customized task in KE-chain.

    :cvar PANEL: panel
    :cvar TOOLBAR: toolbar
    :cvar PROPERTYGRID: propertyGrid
    :cvar SUPERGRID: superGrid
    :cvar PAGINATEDSUPERGRID: paginatedSuperGrid
    :cvar FILTEREDGRID: filteredGrid
    :cvar DISPLAYFIELD: displayfield
    :cvar PROPERTYATTACHMENTPREVIEWER: propertyAttachmentViewer
    :cvar HTMLPANEL: htmlPanel
    :cvar EXECUTESERVICE: executeService
    :cvar NOTEBOOKPANEL: notebookPanel
    :cvar BUTTON: button
    :cvar MODELVIEWER: modelViewer
    :cvar CSVGRID: csvGrid
    :cvar JSONTREE: jsonTree
    """

    PANEL = "panel"
    TOOLBAR = "toolbar"
    PROPERTYGRID = "propertyGrid"
    SUPERGRID = "superGrid"
    PAGINATEDSUPERGRID = "paginatedSuperGrid"
    FILTEREDGRID = "filteredGrid"
    DISPLAYFIELD = "displayfield"
    # in 1.13.1
    PROPERTYATTACHMENTPREVIEWER = "propertyAttachmentViewer"
    HTMLPANEL = "htmlPanel"
    EXECUTESERVICE = "executeService"
    NOTEBOOKPANEL = "notebookPanel"

    # for RND
    BUTTON = "button"
    MODELVIEWER = "modelViewer"
    CSVGRID = "csvGrid"
    JSONTREE = "jsonTree"


class ActivityStatus(Enum):
    """The various Activity statuses that are accepted by KE-chain.

    :cvar OPEN: status of activity is open
    :cvar COMPLETED: status of activity is completed
    """

    OPEN = 'OPEN'
    COMPLETED = 'COMPLETED'


class ScopeStatus(Enum):
    """The various status of a scope.

    :cvar ACTIVE: Status of a scope is active (default)
    :cvar CLOSED: Status of a scope is closed
    :cvar TEMPLATE: Status of a scope is a template (not actively used)
    """

    ACTIVE = 'ACTIVE'
    CLOSED = 'CLOSED'
    TEMPLATE = 'TEMPLATE'


class ServiceType(Enum):
    """The file types of sim script.

    :cvar PYTHON_SCRIPT: service is a python script
    :cvar NOTEBOOK: service is a jupyter notebook
    """

    PYTHON_SCRIPT = 'PYTHON SCRIPT'
    NOTEBOOK = 'NOTEBOOK'


class ServiceEnvironmentVersion(Enum):
    """The acceptable versions of python where services run on.

    :cvar PYTHON_2_7: Service execution environment is a python 2.7 container
    :cvar PYTHON_3_5: Service execution environment is a python 3.5 container
    :cvar PYTHON_3_5_NOTEBOOKS: execution environment is a python 3.5 container with jupyter notebook preinstalled
    """

    PYTHON_2_7 = '2.7'
    PYTHON_3_5 = '3.5'
    PYTHON_3_5_NOTEBOOKS = '3.5_notebook'


class ServiceExecutionStatus(Enum):
    """The acceptable states of a running service.

    :cvar LOADING: Execution is in LOADING state (next RUNNING, FAILED)
    :cvar RUNNING: Execution is in RUNNING state (next COMPLETED, FAILED, TERMINATING)
    :cvar COMPLETED: Execution is in COMPLETED state
    :cvar FAILED: Execution is in FAILED state
    :cvar TERMINATING: Execution is in TERMINATING state (next TERMINATED)
    :cvar TERMINATED: Execution is in TERMINATED state
    """

    LOADING = 'LOADING'
    RUNNING = 'RUNNING'
    COMPLETED = 'COMPLETED'
    FAILED = 'FAILED'
    TERMINATING = 'TERMINATING'
    TERMINATED = 'TERMINATED'


class KechainEnv(Enum):
    """Environment variables that can be set for pykechain.

    :cvar KECHAIN_URL: full url of KE-chain where to connect to eg: 'https://<some>.ke-chain.com'
    :cvar KECHAIN_TOKEN: authentication token for the KE-chain user provided from KE-chain user account control
    :cvar KECHAIN_USERNAME: the username for the credentials
    :cvar KECHAIN_PASSWORD: the password for the credentials
    :cvar KECHAIN_SCOPE: the name of the project / scope. Should be unique, otherwise use scope_id
    :cvar KECHAIN_SCOPE_ID: the UUID of the project / scope.
    :cvar KECHAIN_FORCE_ENV_USE: set to 'true', '1', 'ok', or 'yes' to always use the environment variables.
    :cvar KECHAIN_SCOPE_STATUS: the status of the Scope to retrieve, defaults to None to retrieve all scopes
    """

    KECHAIN_FORCE_ENV_USE = 'KECHAIN_FORCE_ENV_USE'
    KECHAIN_URL = 'KECHAIN_URL'
    KECHAIN_TOKEN = 'KECHAIN_TOKEN'
    KECHAIN_USERNAME = 'KECHAIN_USERNAME'
    KECHAIN_PASSWORD = 'KECHAIN_PASSWORD'
    KECHAIN_SCOPE = 'KECHAIN_SCOPE'
    KECHAIN_SCOPE_ID = 'KECHAIN_SCOPE_ID'
    KECHAIN_SCOPE_STATUS = 'KECHAIN_SCOPE_STATUS'

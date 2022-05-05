from pykechain.utils import __dict__inherited__


class Enum:
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
        return sorted(
            (value, name)
            for (name, value) in __dict__inherited__(cls=cls, stop=Enum).items()
        )

    @classmethod
    def values(cls):
        """Provide a (sorted) list of values."""
        return [value for (value, name) in cls.options()]


class Multiplicity(Enum):
    """The various multiplicities that are accepted by KE-chain.

    For more information on the representation in KE-chain, please consult the KE-chain
    `Part documentation`_.

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

    For more information on the representation in KE-chain, please consult the KE-chain
    `Part documentation`_.

    :cvar INSTANCE: Category of Instance
    :cvar MODEL: Category of Model
    """

    INSTANCE = "INSTANCE"
    MODEL = "MODEL"


class Classification(Enum):
    """The various classification of Parts that are accepted by KE-chain.

    For more information on the representation in KE-chain, please consult the KE-chain
    `Part documentation`_.

    :cvar PRODUCT: Classification of the part object is Product
    :cvar CATALOG: Classification of the part object is a CATALOG

    .. _Part documentation: https://support.ke-chain.com/confluence/dosearchsite.action?
            queryString=concept+part
    """

    PRODUCT = "PRODUCT"
    CATALOG = "CATALOG"
    FORM = "FORM"


class PropertyType(Enum):
    """The various property types that are accepted by KE-chain.

    For more information on the representation in KE-chain, please consult the KE-chain
    `Property documentation`_.

    :cvar CHAR_VALUE: a charfield property (single line text)
    :cvar TEXT_VALUE: text property (long text, may span multiple lines)
    :cvar BOOLEAN_VALUE: a boolean value property (True/False)
    :cvar INT_VALUE: integer property (whole number)
    :cvar FLOAT_VALUE: floating point number property (with digits)
    :cvar DATETIME_VALUE: a datetime value property
    :cvar ATTACHMENT_VALUE: an attachment property
    :cvar LINK_VALUE: url property
    :cvar REFERENCE_VALUE: a reference property, a UUID value referring to other part model

    .. versionadded:: 1.14

    :cvar SINGLE_SELECT_VALUE: single select list property (choose from a list)
    :cvar REFERENCES_VALUE: a multi reference property, a list of UUID values referring to
        other part models

    .. versionadded:: 3.6
    :cvar ACTIVITY_REFERENCES_VALUE: Activity References Property
    :cvar SCOPE_REFERENCES_VALUE: Scope References Property
    :cvar SERVICE_REFERENCES_VALUE: Service Referenes Property
    :cvar TEAM_REFERENCES_VALUE: Team References Property
    :cvar USER_REFERENCES_VALUE: User References Property
    :cvar FORM_REFERENCES_VALUE: Form References Property
    :cvar CONTEXT_REFERENCES_VALUE: Context References Property
    :cvar JSON_VALUE: Generic JSON storage Property
    :cvar GEOJSON_VALUE: GEOJSON property to store map data
    :cvar WEATHER_VALUE: Weather JSON property compatible with the response of weatherapi.com

    .. versionadded:: 3.19
    :cvar STATUS_REFERENCES_VALUE: Status References Property

    .. _Property documentation: https://support.ke-chain.com/confluence/dosearchsite.action?
        queryString=concept+property
    """

    CHAR_VALUE = "CHAR_VALUE"
    TEXT_VALUE = "TEXT_VALUE"
    BOOLEAN_VALUE = "BOOLEAN_VALUE"
    INT_VALUE = "INT_VALUE"
    FLOAT_VALUE = "FLOAT_VALUE"
    DATETIME_VALUE = "DATETIME_VALUE"
    DATE_VALUE = "DATE_VALUE"
    TIME_VALUE = "TIME_VALUE"
    ATTACHMENT_VALUE = "ATTACHMENT_VALUE"
    LINK_VALUE = "LINK_VALUE"
    SINGLE_SELECT_VALUE = "SINGLE_SELECT_VALUE"
    MULTI_SELECT_VALUE = "MULTI_SELECT_VALUE"
    REFERENCE_VALUE = "REFERENCE_VALUE"
    REFERENCES_VALUE = "REFERENCES_VALUE"
    ACTIVITY_REFERENCES_VALUE = "ACTIVITY_REFERENCES_VALUE"
    SCOPE_REFERENCES_VALUE = "SCOPE_REFERENCES_VALUE"
    SERVICE_REFERENCES_VALUE = "SERVICE_REFERENCES_VALUE"
    FORM_REFERENCES_VALUE = "FORM_REFERENCES_VALUE"
    CONTEXT_REFERENCES_VALUE = "CONTEXT_REFERENCES_VALUE"
    STATUS_REFERENCES_VALUE = "STATUS_REFERENCES_VALUE"
    TEAM_REFERENCES_VALUE = "TEAM_REFERENCES_VALUE"
    USER_REFERENCES_VALUE = "USER_REFERENCES_VALUE"
    JSON_VALUE = "JSON_VALUE"
    GEOJSON_VALUE = "GEOJSON_VALUE"
    WEATHER_VALUE = "WEATHER_VALUE"


class ActivityType(Enum):
    """The various Activity types that are accepted by KE-chain.

    .. versionadded:: 2.0

    :cvar TASK: a normal task
    :cvar PROCESS: a subprocess (container) containing other tasks
    """

    PROCESS = "PROCESS"
    TASK = "TASK"


class ActivityClassification(Enum):
    """The classification of Activities that are accepted by KE-chain.

    .. versionadded:: 2.0
    .. versionchanged:: 3.2
       Add 'APP' environment for KE-chain versions > 3.1
    .. versionchanged:: 3.14
       Add 'FORM' envornment for KE-chain versions > v2021.10


    :cvar WORKFLOW: Classification of the activity is WORKFLOW
    :cvar CATALOG: Classification of the activity is CATALOG
    :cvar APP: Classification of the activity is APP
    :cvar FORM: Classification of the activity is FORM
    """

    WORKFLOW = "WORKFLOW"
    CATALOG = "CATALOG"
    APP = "APP"
    FORM = "FORM"


class ActivityRootNames(Enum):
    """The classification of Activities that are accepted by KE-chain.

    .. versionadded:: 2.0
    .. versionchanged:: 3.2
       Add 'APP' environment for KE-chain versions > 3.1
    .. versionchanged:: 3.14
       Add 'FORM' environment for KE-chain versions >= v2021.10

    :cvar WORKFLOW_ROOT: Root of the activity is WORKFLOW_ROOT
    :cvar CATALOG_ROOT: Root of the activity is CATALOG_ROOT (below are CATALOG tasks)
    :cvar APP_ROOT: Root of the activity is APP_ROOT (below are APP 'tasks' ie. 'screems')
    """

    WORKFLOW_ROOT = "WORKFLOW_ROOT"
    CATALOG_ROOT = "CATALOG_ROOT"
    APP_ROOT = "APP_ROOT"
    FORM_ROOT = "FORM_ROOT"


activity_root_name_by_classification = {
    ActivityClassification.WORKFLOW: ActivityRootNames.WORKFLOW_ROOT,
    ActivityClassification.CATALOG: ActivityRootNames.CATALOG_ROOT,
    ActivityClassification.APP: ActivityRootNames.APP_ROOT,
    ActivityClassification.FORM: ActivityRootNames.FORM_ROOT,
}


class WidgetNames(Enum):
    """The various Names of the Widget that can be configured.

    .. versionchanged:: 3.14
       Added FORMMETAPANEL for KE-chain versions >= v2021.10

    :cvar SUPERGRIDWIDGET: superGridWidget
    :cvar PROPERTYGRIDWIDGET: propertyGridWidget
    :cvar HTMLWIDGET: htmlWidget
    :cvar FILTEREDGRIDWIDGET: filteredGridWidget
    :cvar SERVICEWIDGET: serviceWidget
    :cvar NOTEBOOKWIDGET: notebookWidget
    :cvar ATTACHMENTVIEWERWIDGET: attachmentViewerWidget
    :cvar TASKNAVIGATIONBARWIDGET: taskNavigationBarWidget
    :cvar JSONWIDGET: jsonWidget

    # KE-chain 3 only
    :cvar SIGNATUREWIDGET: signatureWidget
    :cvar CARDWIDGET: cardWidget
    :cvar METAPANELWIDGET: metaPanelWidget
    :cvar FORMMETAPANEL: formMetaPanelWidget
    :cvar MULTICOLUMNWIDGET: multiColumnWidget
    :cvar PROGRESSWIDGET: progressWidget
    :cvar TASKSWIDGET: tasksWidget
    :cvar SERVICECARDWIDGET: serviceCardWidget
    :cvar DASHBOARDWIDGET: 'dashboardWidget'
    :cvar SCOPEMEMBERS: 'scopeMembersWidget'
    """

    SUPERGRIDWIDGET = "superGridWidget"
    PROPERTYGRIDWIDGET = "propertyGridWidget"
    HTMLWIDGET = "htmlWidget"
    FILTEREDGRIDWIDGET = "filteredGridWidget"
    SERVICEWIDGET = "serviceWidget"
    NOTEBOOKWIDGET = "notebookWidget"
    ATTACHMENTVIEWERWIDGET = "attachmentViewerWidget"
    TASKNAVIGATIONBARWIDGET = "taskNavigationBarWidget"
    JSONWIDGET = "jsonWidget"
    METAPANELWIDGET = "metaPanelWidget"
    FORMMETAPANELWIDGET = "formMetaPanelWidget"
    MULTICOLUMNWIDGET = "multiColumnWidget"
    SIGNATUREWIDGET = "signatureWidget"
    CARDWIDGET = "cardWidget"
    PROGRESSWIDGET = "progressWidget"
    TASKSWIDGET = "taskWidget"
    SERVICECARDWIDGET = "serviceCardWidget"
    DASHBOARDWIDGET = "dashboardWidget"
    SCOPEMEMBERS = "scopeMembersWidget"


class WidgetTypes(Enum):
    """The various widget types for the widget definitions available to the widget api.

    .. versionchanged:: 3.14
       Added FORMMETAPANEL for KE-chain versions >= v2021.10

    :cvar UNDEFINED: Undefined Widget
    :cvar PROPERTYGRID: Propertygrid widget
    :cvar SUPERGRID: Supergrid widget
    :cvar HTML: Html widget
    :cvar FILTEREDGRID: Filteredgrid widget
    :cvar SERVICE: Service widget
    :cvar NOTEBOOK: Notebook widget
    :cvar ATTACHMENTVIEWER: Attachmentviewer widget
    :cvar TASKNAVIGATIONBAR: Tasknavigationbar widget
    :cvar JSON: Json widget
    :cvar METAPANEL: Metapanel widget
    :cvar FORMMETAPANEL: The FormMetapanel widget
    :cvar MULTICOLUMN: Multicolumn widget
    :cvar SCOPE: Scope widget
    :cvar THIRDPARTY: Thirdparty widget
    :cvar PROGRESS: Progress widget
    :cvar SIGNATURE: Signature widget
    :cvar CARD: Card widget
    :cvar TASKS: Tasks widget
    :cvar WEATHER: Weather widget
    :cvar SERVICECARD: Servicecard widget
    :cvar DASHBOARD: Dashboard widget
    :cvar SCOPEMEMBERS: Scopemembers widget
    """

    UNDEFINED = "UNDEFINED"
    PROPERTYGRID = "PROPERTYGRID"
    SUPERGRID = "SUPERGRID"
    HTML = "HTML"
    FILTEREDGRID = "FILTEREDGRID"
    SERVICE = "SERVICE"
    NOTEBOOK = "NOTEBOOK"
    ATTACHMENTVIEWER = "ATTACHMENTVIEWER"
    TASKNAVIGATIONBAR = "TASKNAVIGATIONBAR"
    JSON = "JSON"
    METAPANEL = "METAPANEL"
    FORMMETAPANEL = "FORMMETAPANEL"
    MULTICOLUMN = "MULTICOLUMN"
    SCOPE = "SCOPE"
    THIRDPARTY = "THIRDPARTY"
    PROGRESS = "PROGRESS"
    SIGNATURE = "SIGNATURE"
    CARD = "CARD"
    TASKS = "TASKS"
    WEATHER = "WEATHER"
    SERVICECARD = "SERVICECARD"
    DASHBOARD = "DASHBOARD"
    SCOPEMEMBERS = "SCOPEMEMBERS"


WidgetCompatibleTypes = {
    WidgetNames.SUPERGRIDWIDGET: WidgetTypes.SUPERGRID,
    WidgetNames.PROPERTYGRIDWIDGET: WidgetTypes.PROPERTYGRID,
    WidgetNames.HTMLWIDGET: WidgetTypes.HTML,
    WidgetNames.FILTEREDGRIDWIDGET: WidgetTypes.FILTEREDGRID,
    WidgetNames.SERVICEWIDGET: WidgetTypes.SERVICE,
    WidgetNames.NOTEBOOKWIDGET: WidgetTypes.NOTEBOOK,
    WidgetNames.ATTACHMENTVIEWERWIDGET: WidgetTypes.ATTACHMENTVIEWER,
    WidgetNames.TASKNAVIGATIONBARWIDGET: WidgetTypes.TASKNAVIGATIONBAR,
    WidgetNames.JSONWIDGET: WidgetTypes.JSON,
    WidgetNames.METAPANELWIDGET: WidgetTypes.METAPANEL,
    WidgetNames.FORMMETAPANELWIDGET: WidgetTypes.FORMMETAPANEL,
    WidgetNames.MULTICOLUMNWIDGET: WidgetTypes.MULTICOLUMN,
    WidgetNames.PROGRESSWIDGET: WidgetTypes.PROGRESS,
    WidgetNames.SIGNATUREWIDGET: WidgetTypes.SIGNATURE,
    WidgetNames.CARDWIDGET: WidgetTypes.CARD,
    WidgetNames.TASKSWIDGET: WidgetTypes.TASKS,
    WidgetNames.SERVICECARDWIDGET: WidgetTypes.SERVICECARD,
    WidgetNames.DASHBOARDWIDGET: WidgetTypes.DASHBOARD,
    WidgetNames.SCOPEMEMBERS: WidgetTypes.SCOPEMEMBERS,
}

default_metapanel_widget = dict(
    name=WidgetNames.METAPANELWIDGET,
    config=dict(),
    meta=dict(
        showAll=True,
    ),
)


class ActivityStatus(Enum):
    """The various Activity statuses that are accepted by KE-chain.

    :cvar OPEN: status of activity is open
    :cvar COMPLETED: status of activity is completed
    """

    OPEN = "OPEN"
    COMPLETED = "COMPLETED"


class ScopeStatus(Enum):
    """The various status of a scope.

    .. versionchanged:: 3.0
      The `TEMPLATE` ScopeStatus is deprecated in KE-chain 3

    :cvar ACTIVE: Status of a scope is active (default)
    :cvar CLOSED: Status of a scope is closed
    :cvar TEMPLATE: Status of a scope is a template (not actively used)(deprecated in KE-chain 3.0)
    :cvar DELETING: Status of a scope when the scope is being deleted
    """

    ACTIVE = "ACTIVE"
    CLOSED = "CLOSED"
    TEMPLATE = "TEMPLATE"
    DELETING = "DELETING"


class ScopeCategory(Enum):
    """The various categories of a scope.

    .. versionadded::3.0

    :cvar LIBRARY_SCOPE: The scope is a library scope
    :cvar USER_SCOPE: The scope is a normal user scope
    :cvar TEMPLATE_SCOPE: The scope is a template scope
    """

    LIBRARY_SCOPE = "LIBRARY_SCOPE"
    USER_SCOPE = "USER_SCOPE"
    TEMPLATE_SCOPE = "TEMPLATE_SCOPE"


class ServiceType(Enum):
    """The file types of sim script.

    :cvar PYTHON_SCRIPT: service is a python script
    :cvar NOTEBOOK: service is a jupyter notebook
    """

    PYTHON_SCRIPT = "PYTHON SCRIPT"
    NOTEBOOK = "NOTEBOOK"


class ServiceEnvironmentVersion(Enum):
    """The acceptable versions of python where services run on.

    :cvar PYTHON_3_6: Service execution environment is a python 3.6 container (unsupported)
    :cvar PYTHON_3_7: Service execution environment is a python 3.7 container
    :cvar PYTHON_3_8: Service execution environment is a python 3.8 container
    :cvar PYTHON_3_9: Service execution environment is a python 3.9 container
    :cvar PYTHON_3_10: Service execution environment is a python 3.10 container
    :cvar PYTHON_3_6_NOTEBOOKS: execution environment is a python 3.6 container with jupyter
        notebook preinstalled (unsupported)
    :cvar PYTHON_3_8_NOTEBOOKS: execution environment is a python 3.8 container with jupyter
        notebook preinstalled
    :cvar PYTHON_3_9_NOTEBOOKS: execution environment is a python 3.9 container with jupyter
        notebook preinstalled
    :cvar PYTHON_3_10_NOTEBOOKS: execution environment is a python 3.10 container with jupyter
        notebook preinstalled
    """

    PYTHON_3_6 = "3.6"  # unsupported
    PYTHON_3_7 = "3.7"
    PYTHON_3_8 = "3.8"
    PYTHON_3_9 = "3.9"
    PYTHON_3_10 = "3.10"
    PYTHON_3_6_NOTEBOOKS = "3.6_notebook"  # unsupported
    PYTHON_3_8_NOTEBOOKS = "3.8_notebook"
    PYTHON_3_9_NOTEBOOKS = "3.9_notebook"
    PYTHON_3_10_NOTEBOOKS = "3.10_notebook"


class ServiceScriptUser(Enum):
    """The acceptable usertypes under which a (trusted) service is run.

    :cvar KENODE_USER: Run as "kenode" user. Equivalent to a manager in a scope.
    :cvar TEAMMANAGER_USER: Run as "kenode_team". Equivalent to a manager in a team.
        (disabled until available)
    :cvar CONFIGURATOR_USER: Run as "kenode_configurator". Equivalent to GG:Configurator.
    """

    KENODE_USER = "kenode"
    # TEAMMANAGER_USER = "kenode_team"
    CONFIGURATOR_USER = "kenode_configurator"


class ServiceExecutionStatus(Enum):
    """The acceptable states of a running service.

    :cvar LOADING: Execution is in LOADING state (next RUNNING, FAILED)
    :cvar RUNNING: Execution is in RUNNING state (next COMPLETED, FAILED, TERMINATING)
    :cvar COMPLETED: Execution is in COMPLETED state
    :cvar FAILED: Execution is in FAILED state
    :cvar TERMINATING: Execution is in TERMINATING state (next TERMINATED)
    :cvar TERMINATED: Execution is in TERMINATED state
    """

    LOADING = "LOADING"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    TERMINATING = "TERMINATING"
    TERMINATED = "TERMINATED"


class TeamRoles(Enum):
    """Roles that exist for a team member.

    :cvar MEMBER: A normal team member
    :cvar MANAGER: A team member that may manage the team (add or remove members, change team)
    :cvar OWNER: The owner of a team
    """

    MEMBER = "MEMBER"
    MANAGER = "MANAGER"
    OWNER = "OWNER"


class ScopeRoles(Enum):
    """
    Roles that exist for a member of a scope.

    :cvar MANAGER: owner of the scope, has full rights
    :cvar SUPERVISOR: supervisor member of a scope, has the rights as leadmember and rights to
        manage catalog tasks.
    :cvar LEADMEMBER: elevated member, has assignment rights, no rights on App tasks or
        Catalog tasks.
    :cvar MEMBER: normal member, only has viewing rights
    """

    MANAGER = "manager"
    SUPERVISOR = "supervisor"
    LEADMEMBER = "leadmember"
    MEMBER = "member"


class ScopeMemberActions(Enum):
    """
    Actions to be performed on the members of a scope.

    :cvar ADD: add a member to the scope
    :cvar REMOVE: delete a member from the scope
    """

    ADD = "add"
    REMOVE = "remove"


class ContextType(Enum):
    """Types of Contexts.

    :cvar STATIC_LOCATION: Geolocation / Featurecollection context with a geolocation.
    :cvar TIME_PERIOD: Time Period Context with start_date and due_date
    :cvar TEXT_LABEL: generic textual label
    """

    STATIC_LOCATION = "STATIC_LOCATION"
    TIME_PERIOD = "TIME_PERIOD"
    TEXT_LABEL = "TEXT_LABEL"


class ContextGroup(Enum):
    """
    Context may have a context_group.

    ..versionadded: 3.11

    This is for context API versions 1.2.0 or later.

    :cvar UNDEFINED: UNDEFINED
    :cvar DISCIPLINE: Discipline, in nl: Discipline
    :cvar ASSET: Asset, in nl: Object, Kunstwerk
    :cvar DEPARTMENT: Department, in nl: Onderdeel, Afdeling
    :cvar PERIOD: Workperiod, in nl: Werkperiode
    :cvar LOCATION: Location, in nl: Locatie
    :cvar PHASE: Phase, in nl: Fase
    :cvar REQUIREMENT: Requirement, in nl: Eis
    :cvar EXTERNALID: External identifier, to be used to provide a generic link to an
        external application
    :cvar WORKPACKAGE: Workpackage, in nl: Werkpakket
    """

    UNDEFINED = "UNDEFINED"
    DISCIPLINE = "DISCIPLINE"  # nl: Discipline
    ASSET = "ASSET"  # nl: Object, Kunstwerk
    DEPARTMENT = "DEPARTMENT"  # nl: Onderdeel, Afdeling
    PERIOD = "WORKPERIOD"  # nl: Werkperiode
    LOCATION = "LOCATION"  # nl: Locatie
    PHASE = "PHASE"  # nl: Fase
    REQUIREMENT = "REQUIREMENT"  # nl: Eis
    EXTERNALID = "EXTERNALID"
    WORKPACKAGE = "WORKPACKAGE"  # nl: Werkpakket


class KechainEnv(Enum):
    """Environment variables that can be set for pykechain.

    :cvar KECHAIN_URL: full url of KE-chain where to connect to eg: 'https://<some>.ke-chain.com'
    :cvar KECHAIN_TOKEN: authentication token for the KE-chain user provided from KE-chain user
        account control
    :cvar KECHAIN_USERNAME: the username for the credentials
    :cvar KECHAIN_PASSWORD: the password for the credentials
    :cvar KECHAIN_SCOPE: the name of the project / scope. Should be unique, otherwise use scope_id
    :cvar KECHAIN_SCOPE_ID: the UUID of the project / scope.
    :cvar KECHAIN_FORCE_ENV_USE: set to 'true', '1', 'ok', or 'yes' to always use the environment
        variables.
    :cvar KECHAIN_SCOPE_STATUS: the status of the Scope to retrieve, defaults to None to retrieve
        all scopes
    :cvar KECHAIN_CHECK_CERTIFICATES: if the certificates of the URL should be checked.
    """

    KECHAIN_FORCE_ENV_USE = "KECHAIN_FORCE_ENV_USE"
    KECHAIN_URL = "KECHAIN_URL"
    KECHAIN_TOKEN = "KECHAIN_TOKEN"
    KECHAIN_USERNAME = "KECHAIN_USERNAME"
    KECHAIN_PASSWORD = "KECHAIN_PASSWORD"
    KECHAIN_SCOPE = "KECHAIN_SCOPE"
    KECHAIN_SCOPE_ID = "KECHAIN_SCOPE_ID"
    KECHAIN_SCOPE_STATUS = "KECHAIN_SCOPE_STATUS"
    KECHAIN_CHECK_CERTIFICATES = "KECHAIN_CHECK_CERTIFICATES"


class SortTable(Enum):
    """The acceptable sorting options for a grid/table.

    :cvar ASCENDING: Table is sorted in ASCENDING ORDER
    :cvar DESCENDING: Table is sorted in DESCENDING ORDER
    """

    ASCENDING = "ASC"
    DESCENDING = "DESC"


class Alignment(Enum):
    """The alignment options for attachment viewer, navigation bar widgets and service widgets.

    :cvar LEFT: Aligned to the left
    :cvar CENTER: Aligned to the center
    :cvar RIGHT: Aligned to the right
    """

    LEFT = "left"
    CENTER = "center"
    RIGHT = "right"


class NavigationBarAlignment(Alignment):
    """The acceptable alignment options for a Navigation Bar Widget."""

    pass


class SidebarItemAlignment(Enum):
    """The acceptable alignment options for sidebar button.

    :cvar TOP: "top"
    :cvar BOTTOM: "bottom"
    """

    TOP = "top"
    BOTTOM = "bottom"


class SidebarButtonAlignment(SidebarItemAlignment):
    """Compatibility enumeration class for the SidebarItemAlignment."""

    pass


class SidebarType(Enum):
    """The types that can exist as a Sidebar Item.

    :cvar BUTTON: a button,
    :cvar CARD: a card
    """

    BUTTON = "BUTTON"
    CARD = "CARD"


class PaperSize(Enum):
    """The acceptable paper sizes options for a downloaded PDF.

    :cvar A0: Paper of size A0
    :cvar A1: Paper of size A1
    :cvar A2: Paper of size A2
    :cvar A3: Paper of size A3
    :cvar A4: Paper of size A4
    """

    A0 = "a0paper"
    A1 = "a1paper"
    A2 = "a2paper"
    A3 = "a3paper"
    A4 = "a4paper"
    AUTO = "automatic"


class PaperOrientation(Enum):
    """The acceptable paper orientation options for a downloaded PDF.

    :cvar PORTRAIT: Paper of orientation 'portrait'
    :cvar LANDSCAPE: Paper of orientation 'landscape'
    """

    PORTRAIT = "portrait"
    LANDSCAPE = "landscape"


class PropertyVTypes(Enum):
    """The VTypes (or validator types) that are allowed in the json.

    This corresponds to the various validator classes which SHOULD be named:
       `vtype[0].upper() + vtype[1:]`
       eg: 'numbericRangeValidator' has an implementation class of 'NumericRangeValidator'

    .. versionadded:: 2.2

    :cvar NONEVALIDATOR: noneValidator - No validation is done
    :cvar NUMERICRANGE: numericRangeValidator
    :cvar BOOLEANFIELD: booleanFieldValidator
    :cvar REQUIREDFIELD: requiredFieldValidator
    :cvar EVENNUMBER: evenNumberValidator
    :cvar ODDNUMBER: oddNumberValidator
    :cvar REGEXSTRING: regexStringValidator
    :cvar SINGLEREFERENCE: 'singleReferenceValidator'
    :cvar FILEEXTENSION: 'fileExtensionValidator'
    :cvar FILESIZE: 'fileSizeValidator'
    """

    NONEVALIDATOR = "noneValidator"
    NUMERICRANGE = "numericRangeValidator"
    BOOLEANFIELD = "booleanFieldValidator"
    REQUIREDFIELD = "requiredFieldValidator"
    EVENNUMBER = "evenNumberValidator"
    ODDNUMBER = "oddNumberValidator"
    REGEXSTRING = "regexStringValidator"
    SINGLEREFERENCE = "singleReferenceValidator"
    FILEEXTENSION = "fileExtensionValidator"
    FILESIZE = "fileSizeValidator"

    # fallback
    ALWAYSALLOW = "alwaysAllowValidator"


class ValidatorEffectTypes(Enum):
    """The effects that can be attached to a validator.

    .. versionadded:: 2.2

    :cvar NONE_EFFECT: noneEffect
    :cvar VISUALEFFECT: visualEffect
    :cvar TEXT_EFFECT: textEffect
    :cvar ERRORTEXT_EFFECT: errorTextEffect
    :cvar HELPTEXT_EFFECT: helpTextEffect
    """

    NONE_EFFECT = "noneEffect"
    VISUALEFFECT = "visualEffect"
    TEXT_EFFECT = "textEffect"
    ERRORTEXT_EFFECT = "errorTextEffect"
    HELPTEXT_EFFECT = "helpTextEffect"


class PropertyRepresentation(Enum):
    """
    The Representation configuration to display a property value.

    .. versionadded:: 3.0
    .. versionchanged:: 3.11 added geocoordinate in line with KE-chain v2021.5.0

    :cvar DECIMAL_PLACES: Amount of decimal places to show the number
    :cvar SIGNIFICANT_DIGITS: Number (count) of significant digits to display the number
    :cvar LINK_TARGET: configuration of a link to open the link in a new browsertab or not.
    :cvar BUTTON: options to represent the choices of a select-list
    :cvar THOUSANDS_SEPARATOR: option to display the thousand separator
    :cvar AUTOFILL: option to autofill the content of the property
    :cvar GEOCOORDINATE: option to display an alternative representation for the geocoordinate
    :cvar USE_PROPERTY_NAME: option to display the name of a property for a part actvity ref prop
    """

    DECIMAL_PLACES = "decimalPlaces"
    SIGNIFICANT_DIGITS = "significantDigits"
    LINK_TARGET = "linkTarget"
    BUTTON = "buttonRepresentation"
    THOUSANDS_SEPARATOR = "thousandsSeparator"
    AUTOFILL = "autofill"
    GEOCOORDINATE = "geoCoordinate"
    USE_PROPERTY_NAME = "usePropertyName"
    CAMERA_SCANNER_INPUT = "cameraScannerInput"


class GeoCoordinateConfig(Enum):
    """GeoCoordinate Configuration Enumerations.

    :cvar APPROX_ADDRESS: represent the coordinate as approximate address (lookup by Google)
    :cvar RD_AMERSFOORT: represent the coordinate as Amersfoort / RN New (epsg: 28992)
    :cvar DD: represent the coordinate as Decimal Degrees (WGS84, epsg:4326)
    :cvar DMS: represent the coordinate as as Degrees Minutes Seconds (WGS84, epsg:4326)

    """

    APPROX_ADDRESS = "approx_address"  # As approximated address
    # Amersfoort/RD (epsg: 28992) https://www.spatialreference.org/ref/epsg/amersfoort-rd-new/
    RD_AMERSFOORT = "rd_amersfoort"
    DD = (
        # As WSG84 (epsg:4326) decimal degrees representation first lat (-90,+90) then lng
        # (-180,+180)
        "dd"
    )
    DMS = (
        # As WSG84 (epsg:4326) degrees, minutes, seconds representation first lat N/S then lng E/W
        "dms"
    )


class OtherRepresentations(Enum):
    """
    Other representations used in KE-chain.

    :cvar CUSTOM_ICON: different font-awesome icons
    """

    CUSTOM_ICON = "customIcon"


class _AllRepresentations(PropertyRepresentation, OtherRepresentations):
    pass


class ShowColumnTypes(Enum):
    """The columns that can be shown in a Property grid.

    .. versionadded:: 2.3

    :cvar UNIT: unit
    :cvar DESCRIPTION: description
    """

    UNIT = "unit"
    DESCRIPTION = "description"


class ScopeWidgetColumnTypes(Enum):
    """The columns that can be shown in a Scope widget grid.

    .. versionadded:: 3.0

    :cvar PROJECT_NAME: Name
    :cvar START_DATE: Start date
    :cvar DUE_DATE: Due date
    :cvar PROGRESS: Progress
    :cvar STATUS: Status
    :cvar TAGS: Tags
    """

    PROJECT_NAME = "Name"
    START_DATE = "Start date"
    DUE_DATE = "Due date"
    PROGRESS = "Progress"
    STATUS = "Status"
    TAGS = "Tags"


class FilterType(Enum):
    """The type of pre-filters that can be set on a Multi Reference Property.

    .. versionadded:: 3.0

    :cvar GREATER_THAN_EQUAL: 'gte'
    :cvar LOWER_THAN_EQUAL: 'lte'
    :cvar CONTAINS: 'icontains'
    :cvar EXACT: 'exact'
    """

    GREATER_THAN_EQUAL = "gte"
    LOWER_THAN_EQUAL = "lte"
    CONTAINS = "icontains"
    CONTAINS_SET = "contains"
    EXACT = "exact"


class ProgressBarColors(Enum):
    """
    Some basic colors that can be set on a Progress Bar inside a Progress Bar Widget.

    .. versionadded:: 3.0

    :cvar BLACK: '#000000'
    :cvar WHITE: '#FFFFFF'
    :cvar RED: 'FF0000'
    :cvar LIME: '#00FF00'
    :cvar BLUE: '#0000FF'
    :cvar YELLOW: '#FFFF00'
    :cvar CYAN: '#00FFFF'
    :cvar MAGENTA: '#FF00FF'
    :cvar SILVER: '#C0C0C0'
    :cvar GRAY: '#808080'
    :cvar MAROON: '#800000'
    :cvar OLIVE: '#808000'
    :cvar GREEN: '#008000'
    :cvar PURPLE: '#800080'
    :cvar TEAL: '#008080'
    :cvar NAVY: '#000080'
    :cvar DEFAULT_COMPLETED: '#339447'
    :cvar DEFAULT_IN_PROGRESS: '#FF6600'
    :cvar DEFAULT_NO_PROGRESS: '#EEEEEE'
    :cvar DEFAULT_IN_PROGRESS_BACKGROUND: '#FC7C3D'
    """

    BLACK = "#000000"
    WHITE = "#FFFFFF"
    RED = "#FF0000"
    LIME = "#00FF00"
    BLUE = "#0000FF"
    YELLOW = "#FFFF00"
    CYAN = "#00FFFF"
    MAGENTA = "#FF00FF"
    SILVER = "#C0C0C0"
    GRAY = "#808080"
    MAROON = "#800000"
    OLIVE = "#808000"
    GREEN = "#008000"
    PURPLE = "#800080"
    TEAL = "#008080"
    NAVY = "#000080"
    DEFAULT_COMPLETED = "#339447"
    DEFAULT_IN_PROGRESS = "#FF6600"
    DEFAULT_NO_PROGRESS = "#EEEEEE"
    DEFAULT_IN_PROGRESS_BACKGROUND = "#FC7C3D"


class LinkTargets(Enum):
    """
    Target for the CardWidget link and Link property representations.

    .. versionadded:: 3.0

    :cvar SAME_TAB: "_self"
    :cvar NEW_TAB: "_blank"
    """

    SAME_TAB = "_self"
    NEW_TAB = "_blank"


class CardWidgetLinkTarget(LinkTargets):
    """Target for the CardWidget, remaining for backwards compatibility."""

    pass


class CardWidgetLinkValue(Enum):
    """
    Link Value for the CardWidget.

    .. versionadded:: 3.0

    :cvar EXTERNAL_LINK: "External link"
    :cvar TASK_LINK: "Task link"
    :cvar NO_LINK: "No link"
    """

    EXTERNAL_LINK = "External link"
    TASK_LINK = "Task link"
    TREE_VIEW = "Tree view"
    NO_LINK = "No link"


class CardWidgetImageValue(Enum):
    """
    Image for the CardWidget.

    .. versionadded:: 3.0

    :cvar CUSTOM_IMAGE: "Custom image"
    :cvar NO_IMAGE: "No image"
    """

    CUSTOM_IMAGE = "Custom image"
    NO_IMAGE = "No image"


class KEChainPages(Enum):
    """
    URL names of built-in KE-chain pages.

    :cvar DETAIL: "detail"
    :cvar FORMS: "forms"
    :cvar TASKS: "activities"
    :cvar WORK_BREAKDOWN: "activitytree"
    :cvar CATALOG_FORMS: "catalogforms"
    :cvar CONTEXTS: "contexts"
    :cvar WORKFLOWS: "workflows"
    :cvar DATA_MODEL: "productmodel"
    :cvar EXPLORER: "product"
    :cvar SERVICES: "scripts"
    """

    DETAIL = "detail"
    FORMS = "forms"
    TASKS = "activities"
    WORK_BREAKDOWN = "activitytree"
    CATALOG_FORMS = "catalogforms"
    CONTEXTS = "contexts"
    WORKFLOWS = "workflows"
    DATA_MODEL = "productmodel"
    EXPLORER = "product"
    SERVICES = "scripts"
    CATALOG_WBS = "catalogtree"
    APP_WBS = "apptree"


KEChainPageLabels = {
    KEChainPages.DETAIL: "Project details",
    KEChainPages.FORMS: "Forms",
    KEChainPages.TASKS: "Tasks",
    KEChainPages.WORK_BREAKDOWN: "Work Breakdown",
    KEChainPages.CATALOG_FORMS: "Template forms",
    KEChainPages.CONTEXTS: "Contexts",
    KEChainPages.WORKFLOWS: "Workflows",
    KEChainPages.CATALOG_WBS: "Catalog",
    KEChainPages.APP_WBS: "App Screens",
    KEChainPages.DATA_MODEL: "Data model",
    KEChainPages.EXPLORER: "Explorer",
    KEChainPages.SERVICES: "Scripts",
}

KEChainPageLabels_nl = {
    KEChainPages.DETAIL: "Project details",
    KEChainPages.FORMS: "Formulieren",
    KEChainPages.TASKS: "Taken",
    KEChainPages.WORK_BREAKDOWN: "Taakverdeling",
    KEChainPages.CATALOG_FORMS: "Sjablonen",
    KEChainPages.CONTEXTS: "Contexten",
    KEChainPages.WORKFLOWS: "Workflows",
    KEChainPages.CATALOG_WBS: "Catalogus",
    KEChainPages.APP_WBS: "App schermen",
    KEChainPages.DATA_MODEL: "Data model",
    KEChainPages.EXPLORER: "Explorer",
    KEChainPages.SERVICES: "Scripts",
}

CardWidgetKEChainPageLink = {
    KEChainPages.DETAIL: "Project",
    KEChainPages.FORMS: "Forms",
    KEChainPages.TASKS: "Tasks",
    KEChainPages.DATA_MODEL: "Model",
    KEChainPages.EXPLORER: "Explorer",
    KEChainPages.SERVICES: "Script",
    KEChainPages.WORK_BREAKDOWN: "Work Breakdown",
    KEChainPages.CATALOG_WBS: "Catalog Tasks",
    KEChainPages.APP_WBS: "App Tasks",
    KEChainPages.CATALOG_FORMS: "Template forms",
    KEChainPages.CONTEXTS: "Contexts",
    KEChainPages.WORKFLOWS: "Workflows",
}

KEChainPageIcons = {
    KEChainPages.DETAIL: "bookmark",
    KEChainPages.FORMS: "file-contract",
    KEChainPages.TASKS: "edit",
    KEChainPages.WORK_BREAKDOWN: "sitemap",
    KEChainPages.CATALOG_FORMS: "file-export",
    KEChainPages.CONTEXTS: "tags",
    KEChainPages.WORKFLOWS: "directions",
    KEChainPages.CATALOG_WBS: "books",
    KEChainPages.APP_WBS: "tablet-alt",
    KEChainPages.DATA_MODEL: "cube",
    KEChainPages.EXPLORER: "folder",
    KEChainPages.SERVICES: "file-code",
}


class SubprocessDisplayMode(Enum):
    """
    URL variations to vary the display of a subprocess activity.

    :cvar ACTIVITIES: "activities"
    :cvar TREEVIEW: "treeview"
    """

    ACTIVITIES = "activities"
    TREEVIEW = "treeview"


class URITarget(Enum):
    """
    Side-bar button redirect options.

    :cvar INTERNAL: "internal"
    :cvar EXTERNAL: "external"
    :cvar NEW: "_new"
    :cvar SELF: "_self"
    :cvar BLANK: "_blank"
    :cvar PARENT: "_parent"
    :cvar TOP: "_top"
    """

    INTERNAL = "internal"
    EXTERNAL = "external"
    NEW = "_new"
    SELF = "_self"
    BLANK = "_blank"
    PARENT = "_parent"
    TOP = "_top"


class FontAwesomeMode(Enum):
    """
    Options to display the same icon.

    Source:
    https://fontawesome.com/how-to-use/on-the-web/setup/getting-started

    :cvar SOLID: "solid"
    :cvar REGULAR: "regular"
    :cvar LIGHT: "light"
    """

    SOLID = "solid"
    REGULAR = "regular"
    LIGHT = "light"


class SidebarAccessLevelOptions(Enum):
    """
    Options for access level options for the sidebar.

    :cvar IS_MEMBER: "is_member"
    :cvar IS_LEAD_MEMBER: "is_leadmember"
    :cvar IS_SUPERVISOR: "is_supervisor"
    :cvar IS_MANAGER: "is_manager"
    """

    IS_MEMBER = "is_member"
    IS_LEAD_MEMBER = "is_leadmember"
    IS_SUPERVISOR = "is_supervisor"
    IS_MANAGER = "is_manager"


class MinimumAccessLevelOptions(SidebarAccessLevelOptions):
    """Options for minumum access level options for the sidebar."""

    pass


class MaximumAccessLevelOptions(SidebarAccessLevelOptions):
    """Options for maximum access level options for the sidebar."""

    pass


class SelectListRepresentations(Enum):
    """
    Options in which a single-select list property options are displayed.

    :cvar DROP_DOWN: "dropdown"
    :cvar CHECK_BOXES: "checkboxes"
    :cvar BUTTONS: "buttons"
    """

    DROP_DOWN = "dropdown"
    CHECK_BOXES = "checkboxes"
    BUTTONS = "buttons"


class ImageFitValue(Enum):
    """
    Options to fit an image on a CardWidget or AttachmentViewerWidget.

    This is a subset from the `object-fit property`_ in HTML.

    :cvar CONTAIN: scale the image to fit within the widget
    :cvar COVER: scale the image to cover the entire widget

    .. _object-fit property: https://developer.mozilla.org/en-US/docs/Web/CSS/object-fit
    """

    CONTAIN = "contain"
    COVER = "cover"


class WidgetTitleValue(Enum):
    """
    Options to configure the title of a widget.

    :cvar DEFAULT: Use the default title of the widget type.
    :cvar NO_TITLE: Show no title.
    :cvar CUSTOM_TITLE: Show a custom title text.
    """

    DEFAULT = "Default"
    NO_TITLE = "No title"
    CUSTOM_TITLE = "Custom title"


class NotificationStatus(Enum):
    """
    Options to retrieve a Notification based on its status.

    normal lifecycle:
    - DRAFT, when a message is first saved to the backend and the status is still in draft.
        next states: READY
    - READY: when the message is ready for processing, it is complete and is to be processed
        next states: PROCESSING
    - PROCESSING: when the message is in the process of being send out
        next states: COMPLETED, FAILED
    - COMPLETED: when the message is successfully sent out
        next states: ARCHIVED
    - FAILED: when the message is not successfully sent out
        next states: ARCHIVED
    - ARCHIVED: when the message is archives and waiting for its deletion against a certain
        retention policy
        next states: None

    :cvar ARCHIVED: "archived" notifications
    :cvar COMPLETED: "completed" notifications
    :cvar DRAFT: "draft" notifications
    :cvar FAILED: "failed" notifications
    :cvar PROCESSING: "processing" notifications
    :cvar READY: "ready" notifications
    """

    ARCHIVED = "ARCHIVED"
    COMPLETED = "COMPLETED"
    DRAFT = "DRAFT"
    FAILED = "FAILED"
    PROCESSING = "PROCESSING"
    READY = "READY"


class NotificationEvent(Enum):
    """
    Options to retrieve a Notification based on its event.

    :cvar SHARE_ACTIVITY_LINK: notifications generated by sharing the link of an `Activity`
    :cvar EXPORT_ACTIVITY_ASYNC: notifications generated by exporting an `Activity`
    :cvar SHARE_ACTIVITY_PDF: notifications generated by sharing the pdf of an `Activity`
    """

    SHARE_ACTIVITY_LINK = "SHARE_ACTIVITY_LINK"
    EXPORT_ACTIVITY_ASYNC = "EXPORT_ACTIVITY_ASYNC"
    SHARE_ACTIVITY_PDF = "SHARE_ACTIVITY_PDF"


class NotificationChannels(Enum):
    """
    Options to retrieve a Notification based on its channel.

    :cvar EMAIL: email notification
    :cvar APP: app notification
    """

    EMAIL = "EMAIL"
    APP = "APP"


class LanguageCodes(Enum):
    """
    Options for the language setting of a user.

    :cvar ENGLISH: English
    :cvar FRENCH: French
    :cvar GERMAN: German
    :cvar DUTCH: Dutch
    :cvar ITALIAN: Italian
    """

    ENGLISH = "en"
    FRENCH = "fr"
    GERMAN = "de"
    DUTCH = "nl"
    ITALIAN = "it"


class ImageSize(Enum):
    """
    Options for the Image Size the picture would be saved as from an Attachment Property.

    :cvar SQXS: SQXS (100, 100)  # pixels square
    :cvar XS: XS (100, )  # pixels width
    :cvar S: S (320, )
    :cvar SQS: SQS (320, 320)
    :cvar M: M (640, )
    :cvar SQM: SQM (640, 640)
    :cvar L: L (1024, )
    :cvar SQL: SQL (1024, 1024)
    :cvar XL: XL (2048, )
    :cvar SQXL: SQXL (2048, 2048)
    :cvar XXL: XXL (4096, )
    :cvar SQXXL: SQXXL (4096, 4096)
    """

    SQXS = "SQXS"
    XS = "XS"
    S = "S"
    SQS = "SQS"
    M = "M"
    SQM = "SQM"
    L = "L"
    SQL = "SQL"
    XL = "XL"
    SQXL = "SQXL"
    XXL = "XXL"
    SQXXL = "SQXXL"


class FormCategory(Enum):
    """
    Options for the Category of a Form.

    :cvar MODEL: Model
    :cvar INSTANCE: Instance
    """

    MODEL = "MODEL"
    INSTANCE = "INSTANCE"


class WorkflowCategory(Enum):
    """
    Options for the Category of a Workflow.

    :cvar CATALOG: Catalog Workflow (immutable)
    :cvar DEFINED: Defined Workflow belonging to a scope
    """

    CATALOG = "CATALOG"
    DEFINED = "DEFINED"


class TransitionType(Enum):
    """
    Options for the Type of a Transition.

    :cvar INITIAL: Initial transition, the initial transition to follow when the form is created.
    :cvar GLOBAL: Global transition, possibility to transition to all statuses from any
    :cvar DIRECTED: A Directed transition, a transition with a specific from -> to direction
    """

    INITIAL = "INITIAL"
    GLOBAL = "GLOBAL"
    DIRECTED = "DIRECTED"


class StatusCategory(Enum):
    """
    Category of statuses.

    :cvar UNDEFINED: Undefined status
    :cvar TODO: Todo status
    :cvar INPROGRESS: In progress status
    :cvar DONE: Done status
    """

    UNDEFINED = "UNDEFINED"
    TODO = "TODO"
    INPROGRESS = "INPROGRESS"
    DONE = "DONE"

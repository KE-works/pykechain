from pykechain.enums import Enum


class DashboardWidgetSourceScopes(Enum):
    """
    Options to link the Dashboard Widget to a source.

    :cvar TAGGED_SCOPES: source is a list of tags
    :cvar CURRENT_SCOPE: source is the current project
    :cvar SELECTED_SCOPES: source is a list of scopes
    :cvar SUBPROCESS: source is an activity
    :cvar OWN_SCOPES: source is list of scopes based on user
    """

    TAGGED_SCOPES = 'taggedScopes'
    CURRENT_SCOPE = 'project'
    SELECTED_SCOPES = 'selectedScopes'
    SUBPROCESS = 'subProcess'
    OWN_SCOPES = 'scopes'


class DashboardWidgetShowTasks(Enum):
    """
    Options to display information about tasks in a Dashboard widget.

    :cvar TOTAL_TASKS: all the tasks
    :cvar CLOSED_TASKS: closed tasks
    :cvar OVERDUE_TASKS: tasks that had their due date in the past
    :cvar UNASSIGNED_TASKS: tasks that have no assignee
    """

    TOTAL_TASKS = "TOTAL_TASKS"
    CLOSED_TASKS = "CLOSED_TASKS"
    OVERDUE_TASKS = "OVERDUE_TASKS"
    UNASSIGNED_TASKS = "UNASSIGNED_TASKS"


class DashboardWidgetShowScopes(Enum):
    """
    Options to display information about scopes in a Dashboard widget.

    :cvar TOTAL_SCOPES: all the projects
    :cvar CLOSED_SCOPES: closed projects
    :cvar OVERDUE_SCOPES: projects that had their due date in the past
    """

    TOTAL_SCOPES = "TOTAL_SCOPES"
    CLOSED_SCOPES = "CLOSED_SCOPES"
    OVERDUE_SCOPES = "OVERDUE_SCOPES"


class AssociatedObjectId(Enum):
    """
    Options to associate object id's to the meta of a widget (e.g. PaginatedGrid).

    :cvar PART_INSTANCE_ID: id of the part instance
    :cvar PARENT_INSTANCE_ID: id of the parent instance
    :cvar PART_MODEL_ID: id of the part model
    :cvar TEAM_ID: id of the team
    :cvar PROPERTY_INSTANCE_ID: id of the property instance
    :cvar SERVICE_ID: id of the service
    :cvar ACTIVITY_ID: id of the activity
    """

    PART_INSTANCE_ID = "partInstanceId"
    PARENT_INSTANCE_ID = "parentInstanceId"
    PART_MODEL_ID = "partModelId"
    TEAM_ID = 'teamId'
    PROPERTY_INSTANCE_ID = "propertyInstanceId"
    SERVICE_ID = "serviceId"
    ACTIVITY_ID = 'activityId'


class MetaWidget(Enum):
    """Options found in the meta of all widgets."""

    # Common
    TITLE = "title"
    SHOW_TITLE_VALUE = "showTitleValue"
    CUSTOM_TITLE = "customTitle"
    SHOW_DESCRIPTION_VALUE = "showDescriptionValue"
    DESCRIPTION_OPTION_NOTHING = "No description"
    DESCRIPTION_OPTION_CUSTOM = "Custom description"
    CUSTOM_DESCRIPTION = "customDescription"
    COLLAPSED = "collapsed"
    COLLAPSIBLE = "collapsible"
    NO_BACKGROUND = "noBackground"
    NO_PADDING = "noPadding"
    IS_DISABLED = "isDisabled"
    IS_MERGED = "isMerged"

    # Prefilters
    PREFILTERS = "prefilters"
    EXCLUDED_PROPERTY_MODELS = "propmodelsExcl"
    PROPERTY_MODELS = "property_models"
    VALUES = "values"
    FILTERS_TYPE = "filters_type"

    # Paginated and Super Grids widgets
    NAME = "name"
    PROPERTY_VALUE_PREFILTER = "property_value"
    SORTED_COLUMN = "sortedColumn"
    SORTED_DIRECTION = "sortDirection"
    SHOW_COLUMNS = 'showColumns'
    SHOW_FILTERS_VALUE = "showCollapseFiltersValue"
    FILTERS_COLLAPSED = "Collapsed"
    FILTERS_EXPANDED = "Expanded"
    COLLAPSE_FILTERS = "collapseFilters"
    CUSTOM_PAGE_SIZE = "customPageSize"
    SHOW_NAME_COLUMN = "showNameColumn"
    SHOW_IMAGES = "showImages"
    VISIBLE_ADD_BUTTON = "addButtonVisible"
    VISIBLE_EDIT_BUTTON = "editButtonVisible"
    VISIBLE_DELETE_BUTTON = "deleteButtonVisible"
    VISIBLE_CLONE_BUTTON = "cloneButtonVisible"
    VISIBLE_DOWNLOAD_BUTTON = "downloadButtonVisible"
    VISIBLE_UPLOAD_BUTTON = "uploadButtonVisible"
    VISIBLE_INCOMPLETE_ROWS = "incompleteRowsVisible"
    EMPHASIZE_ADD_BUTTON = "primaryAddUiValue"
    EMPHASIZE_EDIT_BUTTON = "primaryEditUiValue"
    EMPHASIZE_CLONE_BUTTON = "primaryCloneUiValue"
    EMPHASIZE_DELETE_BUTTON = "primaryDeleteUiValue"

    # ScopeGrid widgets
    VISIBLE_ACTIVE_FILTER = "activeFilterVisible"
    VISIBLE_SEARCH_FILTER = "searchFilterVisible"
    TAGS = "tags"

    # Attachment viewer widgets
    ALIGNMENT = "alignment"
    IMAGE_FIT = "imageFit"
    SHOW_DOWNLOAD_BUTTON = "showDownloadButton"
    SHOW_FULL_SCREEN_IMAGE_BUTTON = "showFullscreenImageButton"

    # Property Grid widget
    SHOW_HEADERS = "showHeaders"
    CUSTOM_HEIGHT = "customHeight"

    # Service Widget and Service Card Widget
    EMPHASIZE_BUTTON = "emphasizeButton"
    SHOW_DOWNLOAD_LOG = "showDownloadLog"
    SHOW_LOG = "showLog"
    BUTTON_TEXT_DEFAULT = "Default"
    BUTTON_NO_TEXT = "No text"
    BUTTON_TEXT_CUSTOM = "Custom text"

    # Progress Bar widget
    COLOR_NO_PROGRESS = "colorNoProgress"
    SHOW_PROGRESS_TEXT = "showProgressText"
    COLOR_IN_PROGRESS = "colorInProgress"
    COLOR_COMPLETED_PROGRESS = "colorCompleted"
    COLOR_IN_PROGRESS_BACKGROUND = "colorInProgressBackground"

    # Signature widget
    SHOW_UNDO_BUTTON = "showUndoButtonValue"
    CUSTOM_UNDO_BUTTON_TEXT = "customUndoText"
    CUSTOM_TEXT = "customText"  # Used for task-navigation bar and signature widgets
    SHOW_BUTTON_VALUE = "showButtonValue"

    # Dashboard Widget
    SOURCE = "source"
    SCOPE_TAG = "scopeTag"
    SCOPE_LIST = "scopeList"
    ORDER = "order"
    SELECTED = "selected"
    SHOW_NUMBERS = "showNumbers"
    SHOW_NUMBERS_PROJECTS = "showNumbersProjects"
    SHOW_ASSIGNEES = "showAssignees"
    SHOW_ASSIGNEES_TABLE = "showAssigneesTable"
    SHOW_OPEN_TASK_ASSIGNEES = "showOpenTaskAssignees"
    SHOW_OPEN_VS_CLOSED_TASKS = "showOpenVsClosedTasks"
    SHOW_OPEN_VS_CLOSED_TASKS_ASSIGNEES = "showOpenClosedTasksAssignees"

    # Card Widget and Service Card Widget
    CUSTOM_IMAGE = "customImage"
    SHOW_IMAGE_VALUE = "showImageValue"
    CUSTOM_LINK = "customLink"
    SHOW_LINK_VALUE = "showLinkValue"

    # Task Navigation Widget
    EMPHASIZED = "emphasized"
    EMPHASIZE = "emphasize"
    LINK = "link"
    SHOW_HEIGHT_VALUE = "showHeightValue"
    TASK_BUTTONS = "taskButtons"

    # Meta Panel Widget
    SHOW_ALL = "showAll"

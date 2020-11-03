from pykechain.enums import Enum


class DashboardWidgetSourceScopes(Enum):
    """
    Options to link the Dashboard Widget to a source.

    :cvar TAGGED_SCOPES: source is a list of tags
    :cvar CURRENT_PROJECT: source is the current project
    :cvar SELECTED_SCOPES: source is a list of scopes
    :cvar SUBPROCESS: source is an activity
    :cvar OWN_SCOPES: source is list of scopes based on user
    """

    TAGGED_SCOPES = 'taggedScopes'
    CURRENT_PROJECT = 'project'
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

    :cvar TOTAL_PROJECTS: all the projects
    :cvar CLOSED_PROJECTS: closed projects
    :cvar OVERDUE_PROJECTS: projects that had their due date in the past
    """

    TOTAL_PROJECTS = "TOTAL_PROJECTS"
    CLOSED_PROJECTS = "CLOSED_PROJECTS"
    OVERDUE_PROJECTS = "OVERDUE_PROJECTS"

from pykechain.models.widgets.widget import Widget
from pykechain.models.widgets.widget_schemas import undefined_meta_schema

# UNDEFINED
# PROPERTYGRID
# SUPERGRID
# HTML
# FILTEREDGRID
# SERVICE
# NOTEBOOK
# ATTACHMENTVIEWER
# MULTIATTACHMENTVIEWER
# TASKNAVIGATIONBAR
# JSON
# METAPANEL
# FORMMETAPANEL
# MULTICOLUMN
# SCOPE_WIDGET
# THIRD_PARTY
# PROGRESS
# SIGNATURE
# CARD =
# WEATHER
# DASHBOARD
# SCOPEMEMBERS
# PROJECTINFO

#
# The names of all the widgets do have a Pattern conforming to the following
#
# rule: "<widget_type_in_undercast_with_first_letter_capitalized>Widget"
# In regex terms: r"[A-Z][a-z]+Widget"
#


class MetapanelWidget(Widget):
    """Metapanel Widget."""


class FormmetapanelWidget(Widget):
    """FormMetapanel Widget."""


class PropertygridWidget(Widget):
    """Propertygrid Widget."""


class UndefinedWidget(Widget):
    """Undefined Widget."""

    schema = undefined_meta_schema


class FilteredgridWidget(Widget):
    """Filteredgrid Widget."""


class SupergridWidget(Widget):
    """Supergrid Widget."""


class AttachmentviewerWidget(Widget):
    """Attachmentviewer Widget."""


class MultiAttachmentviewerWidget(Widget):
    """Multi Attachmentviewer Widget."""


class TasknavigationbarWidget(Widget):
    """Tasknavigationbar Widget."""


class HtmlWidget(Widget):
    """HTML Widget."""


class ServiceWidget(Widget):
    """Service Widget."""


class NotebookWidget(Widget):
    """Notebook Widget."""


class JsonWidget(Widget):
    """JSON Widget."""


class MulticolumnWidget(Widget):
    """Multicolumn Widget."""


class ProgressWidget(Widget):
    """
    Progress bar Widget.

    This widget is deprecated as of June 2024.
    """


class ScopeWidget(Widget):
    """Scope grid Widget."""


class SignatureWidget(Widget):
    """Signature Widget."""


class CardWidget(Widget):
    """Card Widget."""


class ThirdpartyWidget(Widget):
    """Thirdparty Widget."""


class TasksWidget(Widget):
    """Tasks Widget."""


class WeatherWidget(Widget):
    """Weather Widget."""


class ServicecardWidget(Widget):
    """ServiceCard Widget."""


class DashboardWidget(Widget):
    """Dashboard Widget."""


class ScopemembersWidget(Widget):
    """ScopeMembers Widget."""


class ProjectinfoWidget(Widget):
    """Project Info Widget."""

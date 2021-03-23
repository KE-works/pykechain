from pykechain.models.widgets.widget import Widget
from pykechain.models.widgets.widget_schemas import undefined_meta_schema


# UNDEFINED = 'UNDEFINED'
# PROPERTYGRID = 'PROPERTYGRID'
# SUPERGRID = 'SUPERGRID'
# HTML = 'HTML'
# FILTEREDGRID = 'FILTEREDGRID'
# SERVICE = 'SERVICE'
# NOTEBOOK = 'NOTEBOOK'
# ATTACHMENTVIEWER = 'ATTACHMENTVIEWER'
# TASKNAVIGATIONBAR = 'TASKNAVIGATIONBAR'
# JSON = 'JSON'
# METAPANEL = 'METAPANEL'
# MULTICOLUMN = 'MULTICOLUMN'
# SCOPE_WIDGET = 'SCOPE_WIDGET'
# THIRD_PARTY = 'THIRD_PARTY'
# PROGRESS = 'PROGRESS'
# SIGNATURE = 'SIGNATURE'
# CARD = 'CARD'
# WEATHER = 'WEATHER'
# DASHBOARD = 'DASHBOARD'
# SCOPEMEMBERS = 'SCOPEMEMBERS'


class MetapanelWidget(Widget):
    """Metapanel Widget."""


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
    """Progress bar Widget."""


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

from pykechain.models.widgets.widget import Widget

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

from .widget_schemas import (
    attachmentviewer_meta_schema, html_meta_schema, navbar_meta_schema,
    property_grid_meta_schema, service_meta_schema, filteredgrid_meta_schema, supergrid_meta_schema,
    progress_meta_schema, multicolumn_meta_schema, scope_meta_schema, thirdpart_meta_schema, notebook_meta_schema,
    metapanel_meta_schema
)


class MetapanelWidget(Widget):
    """Metapanel Widget."""

    schema = metapanel_meta_schema


class PropertygridWidget(Widget):
    """Propertygrid Widget."""

    schema = property_grid_meta_schema


class UndefinedWidget(Widget):
    """Undefined Widget."""


class FilteredgridWidget(Widget):
    """Filteredgrid Widget."""

    schema = filteredgrid_meta_schema


class SupergridWidget(Widget):
    """Supergrid Widget."""

    schema = supergrid_meta_schema


class AttachmentviewerWidget(Widget):
    """Attachmentviewer Widget."""

    schema = attachmentviewer_meta_schema


class TasknavigationbarWidget(Widget):
    """Tasknavigationbar Widget."""

    schema = navbar_meta_schema


class HtmlWidget(Widget):
    """HTML Widget."""

    schema = html_meta_schema


class ServiceWidget(Widget):
    """Service Widget."""

    schema = service_meta_schema


class NotebookWidget(Widget):
    """Notebook Widget."""

    schema = notebook_meta_schema


class JsonWidget(Widget):
    """JSON Widget."""


class MulticolumnWidget(Widget):
    """Multicolumn Widget."""

    schema = multicolumn_meta_schema


class ProgressWidget(Widget):
    """Progress bar Widget."""

    schema = progress_meta_schema


class ScopeWidget(Widget):
    """Scope grid Widget."""

    schema = scope_meta_schema


class ThirdpartyWidget(Widget):
    """Thirdparty Widget."""

    schema = thirdpart_meta_schema

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
    schema = metapanel_meta_schema

    def __init__(self, json, **kwargs):
        super(MetapanelWidget, self).__init__(json, **kwargs)


class PropertygridWidget(Widget):
    schema = property_grid_meta_schema

    def __init__(self, json, **kwargs):
        super(PropertygridWidget, self).__init__(json, **kwargs)


class UndefinedWidget(Widget):
    def __init__(self, json, **kwargs):
        super(UndefinedWidget, self).__init__(json, **kwargs)


class FilteredgridWidget(Widget):
    schema = filteredgrid_meta_schema

    def __init__(self, json, **kwargs):
        super(FilteredgridWidget, self).__init__(json, **kwargs)


class SupergridWidget(Widget):
    schema = supergrid_meta_schema

    def __init__(self, json, **kwargs):
        super(SupergridWidget, self).__init__(json, **kwargs)


class AttachmentviewerWidget(Widget):
    schema = attachmentviewer_meta_schema

    def __init__(self, json, **kwargs):
        super(AttachmentviewerWidget, self).__init__(json, **kwargs)


class TasknavigationbarWidget(Widget):
    schema = navbar_meta_schema

    def __init__(self, json, **kwargs):
        super(TasknavigationbarWidget, self).__init__(json, **kwargs)


class HtmlWidget(Widget):
    schema = html_meta_schema

    def __init__(self, json, **kwargs):
        super(HtmlWidget, self).__init__(json, **kwargs)


class ServiceWidget(Widget):
    schema = service_meta_schema

    def __init__(self, json, **kwargs):
        super(ServiceWidget, self).__init__(json, **kwargs)


class NotebookWidget(Widget):
    schema = notebook_meta_schema

    def __init__(self, json, **kwargs):
        super(NotebookWidget, self).__init__(json, **kwargs)


class JsonWidget(Widget):
    def __init__(self, json, **kwargs):
        super(JsonWidget, self).__init__(json, **kwargs)


class MulticolumnWidget(Widget):
    schema = multicolumn_meta_schema

    def __init__(self, json, **kwargs):
        super(MulticolumnWidget, self).__init__(json, **kwargs)


class ProgressWidget(Widget):
    schema = progress_meta_schema

    def __init__(self, json, **kwargs):
        super(ProgressWidget, self).__init__(json, **kwargs)


class ScopeWidget(Widget):
    schema = scope_meta_schema

    def __init__(self, json, **kwargs):
        super(ScopeWidget, self).__init__(json, **kwargs)


class ThirdpartyWidget(Widget):
    schema = thirdpart_meta_schema

    def __init__(self, json, **kwargs):
        super(ThirdpartyWidget, self).__init__(json, **kwargs)

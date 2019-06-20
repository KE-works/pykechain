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
from pykechain.models.widgets.widget_schemas import attachmentviewer_meta_schema, html_meta_schema, navbar_meta_schema, \
    property_grid_meta_schema, service_meta_schema, filteredgrid_meta_schema


class MetapanelWidget(Widget):
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
    def __init__(self, json, **kwargs):
        super(NotebookWidget, self).__init__(json, **kwargs)


class JsonWidget(Widget):
    def __init__(self, json, **kwargs):
        super(JsonWidget, self).__init__(json, **kwargs)


class MulticolumnWidget(Widget):
    def __init__(self, json, **kwargs):
        super(MulticolumnWidget, self).__init__(json, **kwargs)


class ProgressWidget(Widget):
    def __init__(self, json, **kwargs):
        super(ProgressWidget, self).__init__(json, **kwargs)


class ScopeWidget(Widget):
    def __init__(self, json, **kwargs):
        super(ScopeWidget, self).__init__(json, **kwargs)


class ThirdpartyWidget(Widget):
    def __init__(self, json, **kwargs):
        super(ThirdpartyWidget, self).__init__(json, **kwargs)

# class XXXWidget(Widget):
#     def __init__(self, json, **kwargs):
#         super(XXXWidget, self).__init__(json, **kwargs)

from pykechain.models.widgets.widget import Widget


class PropertygridWidget(Widget):
    schema = {}

    def __init__(self, json, **kwargs):
        super(PropertygridWidget, self).__init__(json, **kwargs)


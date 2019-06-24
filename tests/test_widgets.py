import json
import os

from pykechain.enums import WidgetTypes
from pykechain.models import Activity
from pykechain.models.widgets import UndefinedWidget

from pykechain.models.widgets.widget import Widget
from pykechain.models.widgets.widgetset import WidgetSet
from tests.classes import TestBetamax, SixTestCase


class TestWidgets(TestBetamax):

    def setUp(self):
        super(TestWidgets, self).setUp()

    def test_retrieve_widgets_in_activity(self):
        activity = self.project.activity('Task - Form + Tables + Service')
        widget_set = activity.widgets()
        self.assertIsInstance(widget_set, WidgetSet)
        for w in widget_set:
            self.assertIsInstance(w, Widget)

    def test_create_widget_in_activity(self):
        activity = self.project.activity('test task')  # type: Activity
        created_widget = self.client.create_widget(
            title="Test_widget",
            activity=activity,
            widget_type=WidgetTypes.UNDEFINED,
            meta={},
            order=100
        )
        self.assertIsInstance(created_widget, UndefinedWidget)
        created_widget.delete()

class TestWidgetsValidation(SixTestCase):

    def test_create_widgets_from_all_widget_test_activity(self):
        """Test a comprehensive list with all widgets created with the form editor. (JUN19)"""
        filepath = os.path.join(os.path.dirname(__file__), 'files', 'test_activity_widgets.json')
        with open(filepath) as fd:
            widget_raw_jsons = json.load(fd)
        for widget in widget_raw_jsons:
            w = Widget.create(json=widget, client=object())
            self.assertIsInstance(w, Widget)

import json
import os

from pykechain.enums import WidgetTypes
from pykechain.models import Activity
from pykechain.models.widgets import UndefinedWidget

from pykechain.models.widgets.widget import Widget
from pykechain.models.widgets.widgets_manager import WidgetsManager
from tests.classes import TestBetamax, SixTestCase


class TestWidgets(TestBetamax):

    def setUp(self):
        super(TestWidgets, self).setUp()

    def test_retrieve_widgets_in_activity(self):
        activity = self.project.activity('Task - Form + Tables + Service')
        widget_set = activity.widgets()
        self.assertIsInstance(widget_set, WidgetsManager)
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
        fn = 'test_activity_widgets.json'

        filepath = os.path.join(os.path.dirname(__file__), 'files', 'widget_tests', fn )
        with open(filepath) as fd:
            widget_raw_jsons = json.load(fd)
        for widget in widget_raw_jsons:
            w = Widget.create(json=widget, client=object())
            self.assertIsInstance(w, Widget)
            self.assertEqual(w.widget_type, widget.get('widget_type'))

    def test_create_widgets_from_all_widget_test_activity_pt2(self):
        """Test another comprehensive list with all widgets created with the form editor. (JUN19)

        In this test the customHeight is set to "800" being a string, not an int.
        """
        fn = "test_activity_widgets_2.json"

        filepath = os.path.join(os.path.dirname(__file__), 'files', 'widget_tests', fn)
        with open(filepath) as fd:
            widget_raw_jsons = json.load(fd)
        for widget in widget_raw_jsons:
            w = Widget.create(json=widget, client=object())
            self.assertIsInstance(w, Widget)
            self.assertEqual(w.widget_type, widget.get('widget_type'))

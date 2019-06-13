from pykechain.models.widget import Widget
from tests.classes import TestBetamax


class TestWidgets(TestBetamax):

    def setUp(self):
        super(TestWidgets, self).setUp()

    def test_retrieve_widgets_in_activity(self):
        activity = self.project.activity('Task - Form + Tables + Service')
        for w in activity.widgets():
            self.assertIsInstance(w, Widget)

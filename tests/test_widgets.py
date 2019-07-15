import json
import os

from pykechain.enums import WidgetTypes, ShowColumnTypes, NavigationBarAlignment
from pykechain.models import Activity
from pykechain.models.widgets import UndefinedWidget, HtmlWidget
from pykechain.models.widgets.widget import Widget
from pykechain.models.widgets.widgets_manager import WidgetsManager
from pykechain.utils import is_uuid
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

    def test_widget_attributes(self):
        attributes = ['_client', '_json_data', 'id', 'created_at', 'updated_at', 'ref',
                      'widget_type', 'title', 'meta', 'order', '_activity_id', '_parent_id',
                      'has_subwidgets', '_scope_id', 'progress']

        obj = self.project.activity('Specify wheel diameter').widgets()[0]
        self.assertIsInstance(obj, Widget)
        for attribute in attributes:
            self.assertTrue(hasattr(obj, attribute),
                            "Could not find '{}' in the object: '{}'".format(attribute, obj.__dict__.keys()))


class TestWidgetsValidation(SixTestCase):

    def test_create_widgets_from_all_widget_test_activity(self):
        """Test a comprehensive list with all widgets created with the form editor. (JUN19)"""
        fn = 'test_activity_widgets.json'

        filepath = os.path.join(os.path.dirname(__file__), 'files', 'widget_tests', fn)
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


class TestWidgetManager(TestBetamax):
    def test_activity_has_metapanel_in_widget_manager(self):
        activity = self.project.activity('Task - Form + Tables + Service')
        widgets = activity.widgets()
        self.assertIsInstance(widgets, WidgetsManager)
        self.assertTrue(len(widgets) >= 5)

        self.assertTrue(widgets[0].widget_type, WidgetTypes.METAPANEL)

    def test_widget_can_be_found_with_uuid_in_widget_manager(self):
        activity = self.project.activity('Task - Form + Tables + Service')
        widgets = activity.widgets()
        metapanel = widgets[0]
        self.assertTrue(metapanel, WidgetTypes.METAPANEL)

        self.assertEqual(widgets[metapanel.id], metapanel)

    def test_widgetmanager_has_activity_and_client(self):
        activity = self.project.activity('Task - Form + Tables + Service')
        widgets = activity.widgets()
        self.assertIsNotNone(widgets._client)
        self.assertIsNotNone(widgets._activity_id)
        self.assertIsInstance(widgets._client, self.client.__class__)
        self.assertTrue(is_uuid(widgets._activity_id))


class TestWidgetManagerInActivity(TestBetamax):
    def setUp(self):
        super(TestWidgetManagerInActivity, self).setUp()
        self.task = self.project.create_activity(name="widget_test_task")  # type: Activity2

        self.frame = self.project.part(name='Frame')
        self.frame_model = self.project.model(name='Frame')

    def tearDown(self):
        # self.task.delete()
        super(TestWidgetManagerInActivity, self).tearDown()

    def test_new_widget_using_widget_manager(self):
        widgets = self.task.widgets()  # type: WidgetsManager

        self.assertEqual(len(widgets), 1)
        metapanel = widgets[0]

        htmlwidget = widgets.create_widget(
            widget_type=WidgetTypes.HTML,
            title="Test HTML widget",
            meta=dict(html="Hello")
        )

        self.assertIsInstance(htmlwidget, HtmlWidget)

    def test_property_grid_with_associations_using_widget_manager(self):
        widgets = self.task.widgets()  # type: WidgetsManager

        widgets.create_widget(
            widget_type=WidgetTypes.PROPERTYGRID,
            title="Frame Property Grid",
            meta=dict(
                activityId=str(self.task.id),
                partInstanceId=str(self.frame.id)
            ),
            writable_models=self.frame_model.properties,
            readable_models=[]
        )

    def test_attachment_widget_with_associations_using_widget_manager(self):
        """
        properties: {
            # attachment
            "propertyInstanceId": {"$ref": "#/definitions/uuidString"},
            "activityId": {"$ref": "#/definitions/uuidString"},
            "alignment": {"$ref": "#/definitions/booleanNull"}
        },
        "required": ["propertyInstanceId", "activityId"]
        :return:
        """
        widgets = self.task.widgets()  # type: WidgetsManager
        foto_property = self.project.property("Picture")

        widgets.create_widget(
            widget_type=WidgetTypes.ATTACHMENTVIEWER,
            title="Attachment Viewer",
            meta=dict(
                activityId=str(self.task.id),
                propertyInstanceId=str(foto_property.id)
            ),
            readable_models=[foto_property.model_id]
        )

    def test_add_super_grid_widget(self):
        widgets = self.task.widgets()  # type: WidgetsManager
        part_model = self.project.model(name='Wheel')
        parent_instance = self.project.part(name='Bike')
        widgets.add_super_grid_widget(
            part_model=part_model,
            parent_instance=parent_instance,
            edit=False,
            emphasize_edit=True,
            all_readable=True,
            incomplete_rows=True
        )

    def test_add_filtered_grid_widget(self):
        widgets = self.task.widgets()  # type: WidgetsManager
        part_model = self.project.model(name='Wheel')
        parent_instance = self.project.part(name='Bike')
        widgets.add_filteredgrid_widget(
            part_model=part_model,
            parent_instance=parent_instance,
            edit=True,
            sort_property=part_model.property(name='Diameter'),
            emphasize_edit=True,
            all_writable=True,
            collapse_filters=False,
        )

    def test_add_attachment_widget(self):
        widgets = self.task.widgets()
        picture_instance = self.project.part('Bike').property('Picture')
        widgets.add_attachmentviewer_widget(
            attachment_property = picture_instance
        )

    def test_add_navbar_widget(self):
        widgets = self.task.widgets()

        activity_1 = self.project.activity('Task - Basic Table')
        activity_2 = self.project.activity('Task - Form')
        activity_3 = self.project.activity('Task - Service Increase Gears')

        bar = [
            {'activityId': activity_1},
            {'activityId': activity_2},
            {'activityId': activity_3}
        ]

        widgets.add_tasknavigationbar_widget(
            activities = bar,
            title="Navbar",
            alignment = NavigationBarAlignment.LEFT
        )

    def test_add_propertygrid_widget(self):
        widget_manager = self.task.widgets()  # type: WidgetsManager
        bike_part = self.project.part(name='Bike')
        widget_manager.add_propertygrid_widget(part_instance=bike_part,
                                         custom_title="Testing the customtitle of a property grid widget",
                                         show_headers=False, show_columns=[ShowColumnTypes.UNIT],
                                         readable_models=bike_part.model().properties[:2],
                                         writable_models=bike_part.model().properties[3:])

    def test_service_widget(self):
        widget_manager = self.task.widgets()  # type: WidgetsManager
        service_gears_successful = self.project.service("Service Gears - Successful")

        widget_manager.add_service_widget(service=service_gears_successful)
        widget_manager.add_service_widget(service=service_gears_successful,
                                          custom_title=None,
                                          custom_button_text="Run this script (Custom!) and no title",
                                          emphasize_run=True,
                                          download_log=True)
        widget_manager.add_service_widget(service=service_gears_successful,
                                          custom_title="Also a custom title, but no log",
                                          custom_button_text="Run this script (Custom!)",
                                          emphasize_run=False,
                                          show_log=False)

import json
import os

from pykechain.enums import WidgetTypes, ShowColumnTypes, NavigationBarAlignment
from pykechain.exceptions import IllegalArgumentError
from pykechain.models import Activity
from pykechain.models.widgets import UndefinedWidget, HtmlWidget, PropertygridWidget, AttachmentviewerWidget, \
    SupergridWidget, FilteredgridWidget, TasknavigationbarWidget, ServiceWidget, NotebookWidget, MulticolumnWidget
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

    def test_widget_meta_attribute_is_not_None(self):
        obj = self.project.activity('Specify wheel diameter').widgets()[0]
        self.assertIsInstance(obj, Widget)
        self.assertIsNotNone(obj.meta)

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
        self.task.delete()
        super(TestWidgetManagerInActivity, self).tearDown()

    def test_new_widget_using_widget_manager(self):
        widget_manager = self.task.widgets()  # type: WidgetsManager

        self.assertEqual(len(widget_manager), 1)
        metapanel = widget_manager[0]

        htmlwidget = widget_manager.create_widget(
            widget_type=WidgetTypes.HTML,
            title="Test HTML widget",
            meta=dict(html="Hello")
        )

        self.assertIsInstance(htmlwidget, HtmlWidget)
        self.assertEqual(len(widget_manager), 1 + 1)

    def test_property_grid_with_associations_using_widget_manager(self):
        widget_manager = self.task.widgets()  # type: WidgetsManager

        widget = widget_manager.create_widget(
            widget_type=WidgetTypes.PROPERTYGRID,
            title="Frame Property Grid",
            meta=dict(
                activityId=str(self.task.id),
                partInstanceId=str(self.frame.id)
            ),
            writable_models=self.frame_model.properties,
            readable_models=[]
        )

        self.assertIsInstance(widget, PropertygridWidget)
        self.assertEqual(len(widget_manager), 1 + 1)

    def test_attachment_widget_with_associations_using_widget_manager(self):
        widget_manager = self.task.widgets()  # type: WidgetsManager
        foto_property = self.project.property("Picture")

        widget = widget_manager.create_widget(
            widget_type=WidgetTypes.ATTACHMENTVIEWER,
            title="Attachment Viewer",
            meta=dict(
                activityId=str(self.task.id),
                propertyInstanceId=str(foto_property.id)
            ),
            readable_models=[foto_property.model_id]
        )

        self.assertIsInstance(widget, AttachmentviewerWidget)
        self.assertEqual(len(widget_manager), 1 + 1)

    def test_add_super_grid_widget(self):
        widget_manager = self.task.widgets()  # type: WidgetsManager
        part_model = self.project.model(name='Wheel')
        parent_instance = self.project.part(name='Bike')

        widget = widget_manager.add_supergrid_widget(
            part_model=part_model,
            parent_instance=parent_instance,
            edit=False,
            emphasize_edit=True,
            all_readable=True,
            incomplete_rows=True
        )

        self.assertIsInstance(widget, SupergridWidget)
        self.assertEqual(len(widget_manager), 1 + 1)

    def test_add_filtered_grid_widget(self):
        widget_manager = self.task.widgets()  # type: WidgetsManager
        part_model = self.project.model(name='Wheel')
        parent_instance = self.project.part(name='Bike')
        widget = widget_manager.add_filteredgrid_widget(
            part_model=part_model,
            parent_instance=parent_instance,
            edit=True,
            # sort_property=part_model.property(name='Diameter'),
            emphasize_edit=True,
            all_writable=True,
            collapse_filters=False,
        )

        self.assertIsInstance(widget, FilteredgridWidget)
        self.assertEqual(len(widget_manager), 1 + 1)

    def test_add_attachment_widget(self):
        widget_manager = self.task.widgets()
        picture_instance = self.project.part('Bike').property('Picture')
        widget = widget_manager.add_attachmentviewer_widget(
            attachment_property=picture_instance
        )

        self.assertIsInstance(widget, AttachmentviewerWidget)
        self.assertEqual(len(widget_manager), 1 + 1)

    def test_add_navbar_widget(self):
        widget_manager = self.task.widgets()

        activity_1 = self.project.activity('Task - Basic Table')
        activity_2 = self.project.activity('Task - Form')
        activity_3 = self.project.activity('Task - Service Increase Gears')

        bar = [
            {'activityId': activity_1},
            {'activityId': activity_2},
            {'activityId': activity_3}
        ]

        widget = widget_manager.add_tasknavigationbar_widget(
            activities=bar,
            title="Navbar",
            alignment=NavigationBarAlignment.LEFT
        )

        self.assertIsInstance(widget, TasknavigationbarWidget)
        self.assertEqual(len(widget_manager), 1 + 1)

    def test_add_propertygrid_widget(self):
        widget_manager = self.task.widgets()  # type: WidgetsManager
        bike_part = self.project.part(name='Bike')
        widget = widget_manager.add_propertygrid_widget(part_instance=bike_part,
                                                        custom_title="Testing the customtitle of a property grid widget",
                                                        show_headers=False, show_columns=[ShowColumnTypes.UNIT],
                                                        readable_models=bike_part.model().properties[:2],
                                                        writable_models=bike_part.model().properties[3:])

        self.assertIsInstance(widget, PropertygridWidget)
        self.assertEqual(len(widget_manager), 1 + 1)

    def test_service_widget(self):
        widget_manager = self.task.widgets()  # type: WidgetsManager
        service_gears_successful = self.project.service("Service Gears - Successful")

        widget1 = widget_manager.add_service_widget(service=service_gears_successful)
        widget2 = widget_manager.add_service_widget(service=service_gears_successful,
                                                    custom_title=None,
                                                    custom_button_text="Run this script (Custom!) and no title",
                                                    emphasize_run=True,
                                                    download_log=True)
        widget3 = widget_manager.add_service_widget(service=service_gears_successful,
                                                    custom_title="Also a custom title, but no log",
                                                    custom_button_text="Run this script (Custom!)",
                                                    emphasize_run=False,
                                                    show_log=False)

        self.assertIsInstance(widget1, ServiceWidget)
        self.assertIsInstance(widget2, ServiceWidget)
        self.assertIsInstance(widget3, ServiceWidget)
        self.assertEqual(len(widget_manager), 1 + 3)

    def test_add_html_widget(self):
        widget_manager = self.task.widgets()  # type: WidgetsManager
        widget = widget_manager.add_html_widget(html='Or is this just fantasy?',
                                                custom_title='Is this the real life?')

        self.assertIsInstance(widget, HtmlWidget)
        self.assertEqual(len(widget_manager), 1 + 1)

    def test_metapanel_widget(self):
        widget_manager = self.task.widgets()  # type: WidgetsManager
        widget_manager.add_metapanel_widget(
            show_all=True,
            show_progress=True,
            show_progressbar=True
        )

        self.assertEqual(len(widget_manager), 1 + 1)

    def test_delete_all_widgets(self):
        """Delete all widgets from an activity"""

        widget_manager = self.task.widgets()  # type: WidgetsManager

        self.assertEqual(len(widget_manager), 1)

        widget_manager.delete_all_widgets()

        self.assertEqual(len(widget_manager), 0)
        self.assertEqual(len(self.task.widgets()), 0)

    def test_delete_widget(self):
        """Delete single widget from an activity"""

        widget_manager = self.task.widgets()  # type: WidgetsManager

        self.assertEqual(len(widget_manager), 1)

        widget_manager.delete_widget(0)

        self.assertEqual(len(widget_manager), 0)
        self.assertEqual(len(self.task.widgets()), 0)

    def test_notebook_widget(self):
        widget_manager = self.task.widgets()  # type: WidgetsManager
        notebook = self.project.service(name="Service Gears - Successful")
        widget1 = widget_manager.add_notebook_widget(notebook=notebook,
                                           custom_title=False)

        widget2 = widget_manager.add_notebook_widget(notebook=notebook,
                                           custom_title="With custom title")

        widget3 = widget_manager.add_notebook_widget(notebook=notebook.id,
                                           custom_title="With no padding and custom height",
                                           customHeight=400,
                                           noPadding=True)

        self.assertIsInstance(widget1, NotebookWidget)
        self.assertIsInstance(widget2, NotebookWidget)
        self.assertIsInstance(widget3, NotebookWidget)
        self.assertEqual(len(widget_manager), 1 + 3)

        with self.assertRaises(IllegalArgumentError):
            widget_manager.add_notebook_widget(notebook="This will raise an error")

    def test_multicolumn_widget(self):
        widget_manager = self.task.widgets()  # type: WidgetsManager
        bike_part = self.project.part('Bike')
        picture_instance = bike_part.property('Picture')
        picture_model = picture_instance.model()
        multi_column_widget = widget_manager.add_multicolumn_widget(custom_title="Multi column Grid + Attachment")

        widget1 = widget_manager.add_propertygrid_widget(part_instance=bike_part,
                                                         writable_models=[picture_model],
                                                         parent_widget=multi_column_widget)

        widget2 = widget_manager.add_attachmentviewer_widget(
            attachment_property=picture_instance, parent_widget=multi_column_widget.id
        )

        self.assertIsInstance(multi_column_widget, MulticolumnWidget)
        self.assertIsInstance(widget1, PropertygridWidget)
        self.assertIsInstance(widget2, AttachmentviewerWidget)
        self.assertEqual(len(widget_manager), 1 + 3)

    def test_insert_widget(self):
        widget_manager = self.task.widgets()  # type: WidgetsManager
        bike_part = self.project.part('Bike')
        w0 = widget_manager[0]  # meta panel
        w1 = widget_manager.add_propertygrid_widget(part_instance=bike_part,
                                                    writable_models=[bike_part.model().properties],
                                                    custom_title="Original widget 1 (w1)")
        w2 = widget_manager.add_propertygrid_widget(part_instance=bike_part,
                                                    writable_models=[bike_part.model().properties],
                                                    custom_title="Original widget 2 (w2)")
        w3 = widget_manager.add_propertygrid_widget(part_instance=bike_part,
                                                    writable_models=[bike_part.model().properties],
                                                    custom_title="Original widget 3 (w3)")

        # if widget order is `[w0,w1,w2]` and inserting `w3` at index 1 (before Widget1);
        #           index:     0 ^1  2
        # the list will be `[w0,w3,w1,w2]`
        widget_manager.insert(1, w3)

        self.assertTrue(w0.widget_type, WidgetTypes.METAPANEL)
        self.assertEqual(widget_manager[w0.id].order, 0)
        self.assertEqual(widget_manager[w3.id].order, 1)
        self.assertEqual(widget_manager[w1.id].order, 2)
        self.assertEqual(widget_manager[w2.id].order, 3)

        added_widget = widget_manager.add_propertygrid_widget(part_instance=bike_part,
                                                              writable_models=[bike_part.model().properties],
                                                              custom_title="Widget Finally Positioned Under Metapanel",
                                                              order=1)

        self.assertEqual(added_widget.order, 1)
        self.assertEqual(widget_manager[w3.id].order, 2)
        self.assertEqual(widget_manager[w1.id].order, 3)
        self.assertEqual(widget_manager[w2.id].order, 4)

    def test_compatibility_functions(self):
        """Testing various compatibility function for equavalence to the 'customization' in WIM1/PIM1"""

        widget_manager = self.task.widgets()  # type: WidgetsManager

        self.assertTrue(hasattr(widget_manager, 'add_text_widget'))
        self.assertTrue(hasattr(widget_manager, 'add_super_grid_widget'))
        self.assertTrue(hasattr(widget_manager, 'add_property_grid_widget'))
        self.assertTrue(hasattr(widget_manager, 'add_paginated_grid_widget'))
        self.assertTrue(hasattr(widget_manager, 'add_script_widget'))
        self.assertTrue(hasattr(widget_manager, 'add_attachment_viewer_widget'))
        self.assertTrue(hasattr(widget_manager, 'add_navigation_bar_widget'))

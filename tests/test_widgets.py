from pykechain.enums import (WidgetTypes, ShowColumnTypes, NavigationBarAlignment, FilterType, ProgressBarColors,
                             Category, LinkTargets, KEChainPages)
from pykechain.exceptions import IllegalArgumentError, APIError
from pykechain.models import Activity2
from pykechain.models.widgets import (UndefinedWidget, HtmlWidget, PropertygridWidget, AttachmentviewerWidget,
                                      SupergridWidget, FilteredgridWidget, TasknavigationbarWidget, SignatureWidget,
                                      ServiceWidget, NotebookWidget,
                                      MulticolumnWidget, CardWidget, MetapanelWidget, ScopeWidget)
from pykechain.models.widgets.widget import Widget
from pykechain.models.widgets.widgets_manager import WidgetsManager
from pykechain.utils import is_uuid
from tests.classes import TestBetamax


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
        activity = self.project.activity('test task')  # type: Activity2
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

    def test_create_widgets(self):
        # setUp
        activity = self.project.activity('test task')
        new_widgets = self.client.create_widgets(widgets=[
            dict(
                activity=activity,
                widget_type=WidgetTypes.HTML,
                title='A new text widget',
                meta=dict(
                    htmlContent='This is HTML text.'
                ),
            ),
            dict(
                activity=activity,
                widget_type=WidgetTypes.HTML,
                title='Another HTML widget',
                meta=dict(
                    htmlContent='They keep on multiplying.'
                ),
            ),
        ])

        # testing
        self.assertIsInstance(new_widgets, list)
        self.assertTrue(all(isinstance(w, Widget) for w in new_widgets))
        self.assertEqual(len(new_widgets), 2)

        # tearDown
        [w.delete() for w in new_widgets]


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
            meta=dict(htmlContent="Hello")
        )

        self.assertIsInstance(metapanel, MetapanelWidget)
        self.assertIsInstance(htmlwidget, HtmlWidget)
        self.assertEqual(len(widget_manager), 1 + 1)

    def test_edit_widget(self):
        widget_manager = self.task.widgets()  # type: WidgetsManager
        bike_part = self.project.part('Bike')
        widget = widget_manager.add_propertygrid_widget(part_instance=bike_part,
                                                        writable_models=bike_part.model().properties)
        import copy
        updated_meta = copy.deepcopy(widget.meta)
        new_title = "My customly edited title"
        updated_meta.update({
            "showTitleValue": "Custom title",
            "customTitle": new_title
        })
        widget_manager[widget.id].edit(meta=updated_meta)

        self.assertEqual(widget_manager[widget.id].meta.get('customTitle'), new_title)

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

        widget = widget_manager.add_attachmentviewer_widget(
            widget_type=WidgetTypes.ATTACHMENTVIEWER,
            title="Attachment Viewer",
            attachment_property=foto_property,
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

    def test_add_filtered_grid_widget_with_prefilters_and_excluded_propmodels(self):
        widget_manager = self.task.widgets()  # type: WidgetsManager
        part_model = self.project.model(name='Wheel')
        parent_instance = self.project.part(name='Bike')
        excluded_propmodels = [part_model.property(name='Spokes')]
        prefilters = dict(
            property_models=[part_model.property(name='Diameter')],
            values=[66],
            filters_type=[FilterType.LOWER_THAN_EQUAL]
        )
        widget = widget_manager.add_filteredgrid_widget(
            part_model=part_model,
            parent_instance=parent_instance,
            edit=True,
            sort_name=True,
            emphasize_edit=True,
            all_writable=True,
            collapse_filters=False,
            prefilters=prefilters,
            excluded_propmodels=excluded_propmodels
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

    def test_add_propertygrid_widget(self):
        widget_manager = self.task.widgets()  # type: WidgetsManager
        bike_part = self.project.part(name='Bike')
        widget = widget_manager.add_propertygrid_widget(part_instance=bike_part,
                                                        title="Testing the custom title of a property grid widget",
                                                        show_headers=False, show_columns=[ShowColumnTypes.UNIT],
                                                        readable_models=bike_part.model().properties[:2],
                                                        writable_models=bike_part.model().properties[3:])

        self.assertIsInstance(widget, PropertygridWidget)
        self.assertEqual(len(widget_manager), 1 + 1)

    def test_add_signature_widget(self):
        widget_manager = self.task.widgets()  # type: WidgetsManager
        bike_part = self.project.part(name='Bike')
        picture = bike_part.property(name='Picture')

        widget1 = widget_manager.add_signature_widget(attachment_property=picture, title="Yes, my precious",
                                                      custom_undo_button_text="Remove za widget",
                                                      custom_button_text="Sign za widget")
        widget2 = widget_manager.add_signature_widget(attachment_property=picture, title=False,
                                                      custom_undo_button_text=False,
                                                      custom_button_text=False)
        widget3 = widget_manager.add_signature_widget(attachment_property=picture)
        self.assertIsInstance(widget1, SignatureWidget)
        self.assertIsInstance(widget2, SignatureWidget)
        self.assertIsInstance(widget3, SignatureWidget)
        self.assertEqual(len(widget_manager), 1 + 3)

        with self.assertRaises(IllegalArgumentError):
            widget_manager.add_signature_widget(attachment_property='Failed script')

    def test_add_card_widget(self):
        # setUp
        widget_manager = self.task.widgets()  # type: WidgetsManager
        bike_part = self.project.part(name='Bike')
        picture = bike_part.property(name='Picture')
        activity = self.project.activity(name='test task')

        widget1 = widget_manager.add_card_widget(title="Some title", description='Some description',
                                                 link='www.ke-chain.com', link_target=LinkTargets.NEW_TAB)
        widget2 = widget_manager.add_card_widget(image=picture, title=False,
                                                 link=activity.id, link_target=LinkTargets.SAME_TAB)

        # testing
        self.assertEqual(len(widget_manager), 1 + 2)

        self.assertIsInstance(widget1, CardWidget)
        self.assertIsInstance(widget2, CardWidget)

        with self.assertRaises(IllegalArgumentError):
            widget_manager.add_card_widget(title=12)

        with self.assertRaises(IllegalArgumentError):
            widget_manager.add_card_widget(description=bike_part)

        with self.assertRaises(IllegalArgumentError):
            widget_manager.add_card_widget(image='this should not work')

        with self.assertRaises(IllegalArgumentError):
            widget_manager.add_card_widget(link=activity, link_target='_somewhere')

        with self.assertRaises(IllegalArgumentError):
            # noinspection PyTypeChecker
            widget_manager.add_card_widget(image_fit=3)

    def test_add_card_widget_ke_chain_pages(self):
        widget_manager = self.task.widgets()  # type: WidgetsManager

        for native_page_name in KEChainPages.values():
            with self.subTest(msg='Page {}'.format(native_page_name)):
                card_widget = widget_manager.add_card_widget(title=native_page_name, link=native_page_name)
                self.assertIsInstance(card_widget, CardWidget)

        self.assertEqual(len(widget_manager), 8, msg='New KE-chain page has been added to the Enum.')

    def test_service_widget(self):
        widget_manager = self.task.widgets()  # type: WidgetsManager
        service_gears_successful = self.project.service("Service Gears - Successful")

        widget1 = widget_manager.add_service_widget(service=service_gears_successful)
        widget2 = widget_manager.add_service_widget(service=service_gears_successful,
                                                    title=None,
                                                    custom_button_text="Run this script (Custom!) and no title",
                                                    emphasize_run=True,
                                                    download_log=True)
        widget3 = widget_manager.add_service_widget(service=service_gears_successful,
                                                    title="Also a custom title, but no log",
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
                                                title='Is this the real life?')

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

    def test_add_metapanel_with_progress_settings(self):
        widget_manager = self.task.widgets()  # type: WidgetsManager
        progress_bar = dict(
            height=15,
            showProgressText=False,
            colorCompleted=ProgressBarColors.RED
        )
        widget_manager.add_metapanel_widget(
            show_all=False,
            show_progress=False,
            show_progressbar=True,
            progress_bar=progress_bar
        )
        self.assertEqual(len(widget_manager), 1 + 1)

    def test_progress_widget(self):
        widget_manager = self.task.widgets()
        widget_manager.add_progress_widget(custom_height=35,
                                           show_progress_text=False)
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
                                                     title=False)

        widget2 = widget_manager.add_notebook_widget(notebook=notebook,
                                                     title="With custom title")

        widget3 = widget_manager.add_notebook_widget(notebook=notebook.id,
                                                     title="With no padding and custom height",
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
        multi_column_widget = widget_manager.add_multicolumn_widget(title="Multi column Grid + Attachment")

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

    def test_scope_widget(self):
        widget_manager = self.task.widgets()  # type: WidgetsManager
        scope_widget = widget_manager.add_scope_widget()

        self.assertIsInstance(scope_widget, ScopeWidget)

    def test_insert_widget(self):
        widget_manager = self.task.widgets()  # type: WidgetsManager
        bike_part = self.project.part('Bike')
        w0 = widget_manager[0]  # meta panel
        w1 = widget_manager.add_propertygrid_widget(part_instance=bike_part,
                                                    writable_models=[bike_part.model().properties],
                                                    title="Original widget 1 (w1)")
        w2 = widget_manager.add_propertygrid_widget(part_instance=bike_part,
                                                    writable_models=[bike_part.model().properties],
                                                    title="Original widget 2 (w2)")
        w3 = widget_manager.add_propertygrid_widget(part_instance=bike_part,
                                                    writable_models=[bike_part.model().properties],
                                                    title="Original widget 3 (w3)")

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
                                                              title="Widget Finally Positioned Under Metapanel",
                                                              order=1)

        self.assertEqual(added_widget.order, 1)
        self.assertEqual(widget_manager[w3.id].order, 2)
        self.assertEqual(widget_manager[w1.id].order, 3)
        self.assertEqual(widget_manager[w2.id].order, 4)

    def test_create_widgets(self):
        # setUp
        widget_manager = self.task.widgets()  # type: WidgetsManager
        new_widgets = widget_manager.create_widgets(widgets=[
            dict(
                widget_type=WidgetTypes.HTML,
                title='A new text widget',
                meta=dict(
                    htmlContent='This is HTML text.'
                ),
            ),
            dict(
                widget_type=WidgetTypes.HTML,
                title='Another HTML widget',
                meta=dict(
                    htmlContent='They keep on multiplying.'
                ),
            ),
        ])

        # testing
        self.assertIsInstance(new_widgets, list)
        self.assertTrue(all(isinstance(w, Widget) for w in new_widgets))
        self.assertEqual(len(new_widgets), 2)

        # tearDown
        [w.delete() for w in new_widgets]

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


class TestWidgetNavigationBarWidget(TestBetamax):

    def setUp(self):
        super(TestWidgetNavigationBarWidget, self).setUp()
        self.task = self.project.create_activity(name="widget_test_task")  # type: Activity2

        self.frame = self.project.part(name='Frame')
        self.frame_model = self.project.model(name='Frame')

        activity_1 = self.project.activity('Task - Basic Table')
        activity_2 = self.project.activity('Task - Form')
        activity_3 = self.project.activity('Task - Service Increase Gears')

        self.nav_bar_config = [
            {'activityId': activity_1, 'emphasize': True},
            {'activityId': activity_2, 'customText': 'Hit me baby!'},
            {'activityId': activity_3}
        ]

    def tearDown(self):
        self.task.delete()
        super(TestWidgetNavigationBarWidget, self).tearDown()

    def test_add_navbar_widget(self):
        widget_manager = self.task.widgets()

        widget = widget_manager.add_tasknavigationbar_widget(
            activities=self.nav_bar_config,
            title="Navbar",
            alignment=NavigationBarAlignment.LEFT
        )

        self.assertIsInstance(widget, TasknavigationbarWidget)
        self.assertEqual(len(widget_manager), 1 + 1)

    def test_add_navbar_widget_in_place(self):
        """
        Test whether the inputs to the function are updated in-place (incorrect) or not (correct).
        For example, activity objects are replaced by their IDs and customText is converted to a string.
        """

        widget_manager = self.task.widgets()

        self.nav_bar_config[0]['customText'] = False

        import copy
        original_bar = copy.deepcopy(self.nav_bar_config)

        widget_manager.add_tasknavigationbar_widget(
            activities=self.nav_bar_config,
            alignment=NavigationBarAlignment.LEFT,
        )

        self.assertEqual(original_bar, self.nav_bar_config)

    def test_add_navbar_widget_incorrect_keys(self):
        widget_manager = self.task.widgets()

        self.nav_bar_config[0]['emphasizeButton'] = True

        with self.assertRaises(IllegalArgumentError):
            widget_manager.add_tasknavigationbar_widget(
                activities=self.nav_bar_config,
                alignment=NavigationBarAlignment.LEFT,
            )

    def test_add_navbar_external_link(self):
        widget_manager = self.task.widgets()

        link = 'https://www.google.com'

        button_1 = self.nav_bar_config[0]
        button_1.pop('activityId')
        button_1['link'] = link

        widget = widget_manager.add_tasknavigationbar_widget(
            activities=self.nav_bar_config,
            alignment=NavigationBarAlignment.LEFT,
        )

        self.assertEqual(widget.meta['taskButtons'][0]['link'], link)

    def test_add_navbar_disabled_button(self):
        widget_manager = self.task.widgets()

        button_1 = self.nav_bar_config[0]
        button_1['isDisabled'] = True

        widget = widget_manager.add_tasknavigationbar_widget(
            activities=self.nav_bar_config,
            alignment=NavigationBarAlignment.LEFT,
        )

        self.assertTrue(widget.meta['taskButtons'][0]['isDisabled'])


class TestWidgetsCopyMove(TestBetamax):
    def setUp(self):
        super(TestWidgetsCopyMove, self).setUp()
        self.task = self.project.create_activity(name="widget_test_task")  # type: Activity2
        self.task_2 = self.project.create_activity(name="test_copy_widget")  # type: Activity2

    def tearDown(self):
        self.task.delete()
        self.task_2.delete()
        super(TestWidgetsCopyMove, self).tearDown()

    def test_copy_widget(self):
        # setUp
        title = "Widget to copy"
        bike_part = self.project.part('Bike')
        widget_manager = self.task.widgets()  # type: WidgetsManager
        widget_1 = widget_manager.add_propertygrid_widget(part_instance=bike_part, all_writable=True,
                                                          title=title)
        widget_1.copy(target_activity=self.task_2, order=0)
        widget_manager_2 = self.task_2.widgets()  # type: WidgetsManager
        associated_model = widget_manager_2[0].parts(category=Category.MODEL)[0]

        # testing
        self.assertEqual(widget_manager_2[0].widget_type, WidgetTypes.PROPERTYGRID)
        self.assertEqual(widget_manager_2[0].title, title)
        self.assertTrue(all(prop.output for prop in associated_model.properties))
        self.assertEqual(len(self.task.widgets()), 2)

    def test_copy_widget_with_wrong_target(self):
        # setUp
        title = "Widget to copy"
        bike_part = self.project.part('Bike')
        widget_manager = self.task.widgets()  # type: WidgetsManager
        widget_1 = widget_manager.add_propertygrid_widget(part_instance=bike_part, all_writable=True,
                                                          title=title)

        # testing
        with self.assertRaises(IllegalArgumentError):
            widget_1.copy(target_activity=self.project, order=0)

    def test_move_widget(self):
        # setUp
        title = "Widget to move"
        bike_part = self.project.part('Bike')
        widget_manager = self.task.widgets()  # type: WidgetsManager
        widget_1 = widget_manager.add_propertygrid_widget(part_instance=bike_part, all_writable=True,
                                                          title=title)
        widget_1.move(target_activity=self.task_2, order=0)
        widget_manager_2 = self.task_2.widgets()  # type: WidgetsManager
        associated_model = widget_manager_2[0].parts(category=Category.MODEL)[0]

        # testing
        self.assertEqual(widget_manager_2[0].widget_type, WidgetTypes.PROPERTYGRID)
        self.assertEqual(widget_manager_2[0].title, title)
        self.assertTrue(all(prop.output for prop in associated_model.properties))
        self.assertEqual(len(self.task.widgets()), 1)


class TestAssociations(TestBetamax):

    def setUp(self):
        super().setUp()
        self.task = self.project.create_activity(name="widget_test_task")  # type: Activity2

        # Exactly 1 model
        self.frame = self.project.part(name='Frame')
        self.frame_model = self.project.model(name='Frame')

        # Zero or more model
        self.wheel_parent = self.project.model(name='Bike')
        self.wheel_model = self.project.model(name='Wheel')

        widgets_manager = self.task.widgets()
        self.form_widget = widgets_manager.add_propertygrid_widget(
            part_instance=self.frame,
            readable_models=self.frame_model.properties,
            writable_models=[],
        )

        self.table_widget = widgets_manager.add_supergrid_widget(
            part_model=self.wheel_model,
            parent_instance=self.wheel_parent,
            readable_models=[],
            writable_models=self.frame_model.properties,
        )

    def tearDown(self):
        self.task.delete()
        super().tearDown()

    def test_update_associations_empty(self):
        self.client.update_widgets_associations(
            widgets=[self.form_widget],
            associations=[([], [])],
        )

    def test_update_widget_associations(self):
        self.client.update_widget_associations(
            widget=self.form_widget,
            readable_models=[],
            writable_models=self.frame_model.properties,
        )

    def test_input_lengths(self):
        with self.assertRaises(IllegalArgumentError):
            self.client.update_widgets_associations(
                widgets=list(self.task.widgets()),
                associations=[([], [])],
            )

    def test_widget_inputs(self):
        with self.assertRaises(IllegalArgumentError):
            self.client.update_widget_associations(
                widget='Not a widget',
            )

    def test_readable_models(self):
        self.client.update_widget_associations(
            widget=self.form_widget,
            readable_models=self.frame_model.properties,
        )

        self.client.update_widget_associations(
            widget=self.table_widget,
            readable_models=self.wheel_model.properties,
        )

        with self.assertRaises(APIError):
            self.client.update_widget_associations(
                widget=self.table_widget,
                readable_models=self.frame.properties,
            )

    def test_writable_models(self):
        self.client.update_widget_associations(
            widget=self.form_widget,
            writable_models=self.frame_model.properties,
        )

        self.client.update_widget_associations(
            widget=self.table_widget,
            writable_models=self.wheel_model.properties,
        )

        with self.assertRaises(APIError):
            self.client.update_widget_associations(
                widget=self.table_widget,
                writable_models=self.frame.properties,
            )

from pykechain.models.customization import ExtCustomization
from pykechain.exceptions import IllegalArgumentError
from pykechain.enums import SortTable, NavigationBarAlignment, ShowColumnTypes
from tests.classes import TestBetamax


class TestExtCustomization(TestBetamax):
    """ Test the customization of activities """

    def setUp(self):
        super(TestExtCustomization, self).setUp()

        self.widgets_test_task = self.project.activity(name='Task to test all widgets')
        self.customization = self.widgets_test_task.customization()
        self.models, self.instances = self.widgets_test_task.associated_parts()
        self.customization.delete_all_widgets()

    def test_get_customization_of_non_customized_task(self):
        """
        Test if an activity has a customization
        """
        self.assertIsInstance(self.customization, ExtCustomization,
                              "The activity customization should be an instance of 'ExtCustomization'")
        self.assertTrue(hasattr(self.customization, "activity"), "The customization object should have a activity")
        self.assertEqual(self.customization.activity.id, self.widgets_test_task.id,
                         "The activity id of the customization object should be the same as the id of the activity")
        self.assertTrue(len(self.customization.widgets()) == 0, "The customizations should have no widgets")

        # tearDown
        self.customization.delete_all_widgets()

    def test_add_json_widget(self):
        """
        Test if a Json Widget can be added to the customization
        """
        self.customization.add_json_widget(dict(xtype="displayfield", value="Some text"))

        self.assertEqual(len(self.customization.widgets()), 1, "The customization should have 1 widget")
        self.assertTrue(self.customization.widgets()[0]["name"] == "jsonWidget",
                        "The first widget should be a jsonWidget")

        # tearDown
        self.customization.delete_all_widgets()

    def test_add_property_grid_widget(self):
        """
        Test if a Property Grid Widget can be added to the customization
        """
        self.customization.add_property_grid_widget(self.instances[0])
        self.customization.add_property_grid_widget(self.instances[0].id)

        self.assertEqual(len(self.customization.widgets()), 2, "The customization should have 1 widget")
        self.assertTrue(self.customization.widgets()[0]["name"] == "propertyGridWidget",
                        "The first widget should be a propertyGridWidget")

        with self.assertRaises(IllegalArgumentError):
            self.customization.add_property_grid_widget(part_instance='This will not work, needs UUID or Part')

        # tearDown
        self.customization.delete_all_widgets()

    def test_add_property_grid_widget_with_max_height(self):
        """
        Test if a Property Grid Widget can be added to the customization with a max height
        """
        self.customization.add_property_grid_widget(self.instances[0], 20)

        self.assertEqual(len(self.customization.widgets()), 1, "The customization should have 1 widget")
        self.assertTrue(self.customization.widgets()[0]["name"] == "propertyGridWidget",
                        "The first widget should be a propertyGridWidget")
        self.assertEqual(self.customization.widgets()[0]["config"]["height"], 20,
                         "The max height property of the config should be 20")

        # tearDown
        self.customization.delete_all_widgets()

    def test_add_property_grid_widget_with_custom_title(self):
        """
        Test if a Property Grid Widget can be added to the customization with a custom title
        """
        custom_title = "my title"

        self.customization.add_property_grid_widget(self.instances[0], None, custom_title)

        self.assertEqual(len(self.customization.widgets()), 1, "The customization should have 1 widget")
        self.assertTrue(self.customization.widgets()[0]["name"] == "propertyGridWidget",
                        "The first widget should be a propertyGridWidget")
        self.assertTrue(self.customization.widgets()[0]["config"]["title"] == custom_title,
                        "The title property of the config should be {}".format(custom_title))

        # tearDown
        self.customization.delete_all_widgets()

    def test_add_property_grid_widget_with_no_title(self):
        """
        Test if a Property Grid Widget can be added to the customization without a title
        """
        self.customization.add_property_grid_widget(self.instances[0], max_height=None, custom_title=None)

        self.assertEqual(len(self.customization.widgets()), 1, "The customization should have 1 widget")
        self.assertTrue(self.customization.widgets()[0]["name"] == "propertyGridWidget",
                        "The first widget should be a propertyGridWidget")
        self.assertEqual(self.customization.widgets()[0]["config"]["title"], str(),
                         "The config should not have a title")

        # tearDown
        self.customization.delete_all_widgets()

    def test_add_property_grid_widget_with_columns_and_headers(self):
        """
        Test if a Property Grid Widget can be added to the customization with our without columns and headers.
        """
        self.customization.add_property_grid_widget(self.instances[0], show_headers=False, show_columns=None)
        self.customization.add_property_grid_widget(self.instances[0], show_headers=True,
                                                    show_columns=[ShowColumnTypes.DESCRIPTION, ShowColumnTypes.UNIT])

        self.assertEqual(len(self.customization.widgets()), 2, "The customization should have 2 widgets")
        self.assertTrue(ShowColumnTypes.DESCRIPTION in
                        self.customization.widgets()[0]["config"]["viewModel"]["data"]["displayColumns"] and
                        not self.customization.widgets()[0]["config"]["viewModel"]["data"]["displayColumns"]
                        [ShowColumnTypes.DESCRIPTION])
        self.assertTrue(ShowColumnTypes.UNIT in
                        self.customization.widgets()[0]["config"]["viewModel"]["data"]["displayColumns"] and
                        not self.customization.widgets()[0]["config"]["viewModel"]["data"]["displayColumns"]
                        [ShowColumnTypes.UNIT])
        self.assertTrue(self.customization.widgets()[0]["config"]["hideHeaders"])

        self.assertTrue(ShowColumnTypes.DESCRIPTION in
                        self.customization.widgets()[1]["config"]["viewModel"]["data"]["displayColumns"] and
                        self.customization.widgets()[1]["config"]["viewModel"]["data"]["displayColumns"]
                        [ShowColumnTypes.DESCRIPTION])
        self.assertTrue(ShowColumnTypes.UNIT in
                        self.customization.widgets()[1]["config"]["viewModel"]["data"]["displayColumns"] and
                        self.customization.widgets()[1]["config"]["viewModel"]["data"]["displayColumns"]
                        [ShowColumnTypes.UNIT])
        self.assertFalse(self.customization.widgets()[1]["config"]["hideHeaders"])

        # tearDown
        self.customization.delete_all_widgets()

    def test_delete_a_widget(self):
        """
        Test if a widget can be deleted by index
        """
        self.customization.add_property_grid_widget(self.instances[0])
        self.customization.add_property_grid_widget(self.instances[1])

        self.assertEqual(len(self.customization.widgets()), 2, "The customization should have 2 widget")
        self.assertTrue(self.customization.widgets()[1]["name"] == "propertyGridWidget",
                        "The second widget should be a propertyGridWidget")

        self.customization.delete_widget(1)

        self.assertEqual(len(self.customization.widgets()), 1, "The customization should have 1 widget")
        self.assertTrue(self.customization.widgets()[0]["name"] == "propertyGridWidget",
                        "The first widget should be a propertyGridWidget")

        # tearDown
        self.customization.delete_all_widgets()

    def test_raise_error_when_delete_a_widget_of_empty_customization(self):
        """
        Test if an error is raised when trying to delete a widget when there are no widgets customized
        """
        self.assertEqual(len(self.customization.widgets()), 0, "The customization should have no widgets")

        with self.assertRaises(ValueError):
            self.customization.delete_widget(0)

        # tearDown
        self.customization.delete_all_widgets()

    def test_delete_all_widgets(self):
        """
        Test if all widgets can be deleted
        """
        self.customization.add_property_grid_widget(self.instances[0])
        self.customization.add_property_grid_widget(self.instances[1])

        self.assertEqual(len(self.customization.widgets()), 2, "The customization should have 2 widget")

        self.customization.delete_all_widgets()

        self.assertEqual(len(self.customization.widgets()), 0, "The customization should have no widgets")

        # tearDown
        self.customization.delete_all_widgets()

    def test_add_text_widget(self):
        """
        Test if a Text Widget can be added
        """
        self.customization.add_text_widget(text='This widget has text', custom_title='This widget also has title',
                                           collapsible=True)
        self.customization.add_text_widget(collapsible=False, collapsed=True)
        widgets = self.customization.widgets()
        self.assertEqual(len(widgets), 2, "The customization should have 2 widgets")
        self.assertTrue(widgets[0]['name'] == 'htmlWidget')
        self.assertTrue(widgets[0]['config']['html'] == 'This widget has text')
        self.assertTrue(widgets[0]['config']['title'] == 'This widget also has title')
        self.assertTrue(widgets[0]['config']['collapsible'])
        self.assertFalse(widgets[0]['config']['collapsed'])

        self.assertFalse('html' in widgets[1]['config'].keys())
        self.assertFalse(widgets[1]['config']['title'])
        self.assertFalse(widgets[1]['config']['collapsible'])
        self.assertFalse(widgets[1]['config']['collapsed'])

        # tearDown
        self.customization.delete_all_widgets()

    def test_add_super_grid_widget(self):
        """
        Test if a Super Grid Widget can be added
        """
        part_model = [model for model in self.models if model.name == 'Spoke'][0]
        sort_property = part_model.property(name='Length')
        parent_instance = [instance for instance in self.instances if instance.name == 'Front Wheel'][0]
        wrong_sort_property = parent_instance.model().property(name='Diameter')
        self.customization.add_super_grid_widget(part_model=part_model, parent_part_instance=parent_instance,
                                                 max_height=800, custom_title='This grid has title, height and parent',
                                                 new_instance=True, emphasize_new_instance=True, emphasize_edit=True)
        self.customization.add_super_grid_widget(part_model=part_model.id, parent_part_instance=parent_instance.id,
                                                 custom_title=None, delete=True, edit=False, export=False,
                                                 incomplete_rows=False, sort_property=sort_property)
        self.customization.add_super_grid_widget(part_model=part_model, sort_property=sort_property.id,
                                                 sort_direction=SortTable.DESCENDING)
        with self.assertRaises(IllegalArgumentError):
            self.customization.add_super_grid_widget(part_model=part_model, new_instance=True)
        with self.assertRaises(IllegalArgumentError):
            self.customization.add_super_grid_widget(part_model=part_model, sort_property=wrong_sort_property)
        with self.assertRaises(IllegalArgumentError):
            self.customization.add_super_grid_widget(part_model='This will not work, needs UUID or Part')
        with self.assertRaises(IllegalArgumentError):
            self.customization.add_super_grid_widget(part_model=part_model, parent_part_instance='Errors triggered')
        with self.assertRaises(IllegalArgumentError):
            self.customization.add_super_grid_widget(part_model=part_model, sort_property='Errors triggered')

        widgets = self.customization.widgets()
        self.assertEqual(len(widgets), 3, "The customization should have 3 super grid widgets")

        # tearDown
        self.customization.delete_all_widgets()

    def test_add_paginated_grid_widget(self):
        part_model = [model for model in self.models if model.name == 'Spoke'][0]
        sort_property = part_model.property(name='Length')
        parent_instance = [instance for instance in self.instances if instance.name == 'Front Wheel'][0]
        wrong_sort_property = parent_instance.model().property(name='Diameter')
        self.customization.add_paginated_grid_widget(part_model=part_model, parent_part_instance=parent_instance,
                                                     max_height=800, custom_title='Grid has title, height and parent',
                                                     new_instance=True, emphasize_new_instance=True,
                                                     emphasize_edit=True)
        self.customization.add_paginated_grid_widget(part_model=part_model.id, parent_part_instance=parent_instance.id,
                                                     custom_title=None, delete=True, edit=False, export=False,
                                                     sort_property=sort_property.id, page_size=2)
        self.customization.add_paginated_grid_widget(part_model=part_model, sort_property=sort_property,
                                                     sort_direction=SortTable.DESCENDING, collapse_filters=True)
        with self.assertRaises(IllegalArgumentError):
            self.customization.add_paginated_grid_widget(part_model=part_model, new_instance=True)
        with self.assertRaises(IllegalArgumentError):
            self.customization.add_paginated_grid_widget(part_model=part_model, sort_property=wrong_sort_property)
        with self.assertRaises(IllegalArgumentError):
            self.customization.add_paginated_grid_widget(part_model='This will not work, needs UUID or Part')
        with self.assertRaises(IllegalArgumentError):
            self.customization.add_paginated_grid_widget(part_model=part_model, parent_part_instance='Errors triggered')
        with self.assertRaises(IllegalArgumentError):
            self.customization.add_paginated_grid_widget(part_model=part_model, sort_property='Errors triggered')

        widgets = self.customization.widgets()
        self.assertEqual(len(widgets), 3, "The customization should have 3 super grid widgets")

        # tearDown
        self.customization.delete_all_widgets()

    def test_add_script_widget(self):
        script = self.project.service(name="Debug pykechain")

        self.customization.add_script_widget(script=script, custom_title='This script has a custom title but no text '
                                             'on the button', custom_button_text=None, emphasize_run=False)
        self.customization.add_script_widget(script=script.id, custom_title=False, custom_button_text='The button has'
                                             ' text, and the title should be default')
        self.customization.add_script_widget(script=script.id, custom_title=None, custom_button_text=False)
        with self.assertRaises(IllegalArgumentError):
            self.customization.add_script_widget(script="This will raise an error")

        widgets = self.customization.widgets()

        self.assertEqual(len(widgets), 3, "The customization should have 3 script widgets")

        # tearDown
        self.customization.delete_all_widgets()

    def test_add_notebook_widget(self):
        notebook = self.project.service(name="Notebook test")

        self.customization.add_notebook_widget(notebook=notebook, custom_title='This script has a custom title and a '
                                               'specified height', height=300)
        self.customization.add_notebook_widget(notebook=notebook.id, custom_title=False, height=400)
        self.customization.add_notebook_widget(notebook=notebook, custom_title=None)

        with self.assertRaises(IllegalArgumentError):
            self.customization.add_notebook_widget(notebook="This will raise an error")

        widgets = self.customization.widgets()

        self.assertEqual(len(widgets), 3, "The customization should have 3 notebook widgets")

        # tearDown
        self.customization.delete_all_widgets()

    def test_add_attachment_viewer_widget(self):
        part_model = [model for model in self.models if model.name == 'Wheel'][0]
        wrong_prop_because_model = part_model.property(name='Wheel image')
        part_instance = [instance for instance in self.instances if instance.name == 'Front Wheel'][0]
        wrong_prop_because_not_attachment = part_instance.property(name='Diameter')
        correct_prop = part_instance.property(name='Wheel image')

        self.customization.add_attachment_viewer_widget(attachment_property=correct_prop, custom_title='This viewer '
                                                        'has a custom title and a specified height', height=900)
        self.customization.add_attachment_viewer_widget(attachment_property=correct_prop.id, custom_title=False,
                                                        height=200)
        self.customization.add_attachment_viewer_widget(attachment_property=correct_prop.id, custom_title=None)

        with self.assertRaises(IllegalArgumentError):
            self.customization.add_attachment_viewer_widget(attachment_property="This will raise an error")
        with self.assertRaises(IllegalArgumentError):
            self.customization.add_attachment_viewer_widget(attachment_property=wrong_prop_because_model)
        with self.assertRaises(IllegalArgumentError):
            self.customization.add_attachment_viewer_widget(attachment_property=wrong_prop_because_not_attachment.id)

        widgets = self.customization.widgets()
        self.assertEqual(len(widgets), 3, "The customization should have 3 attachment viewer widgets")

        # tearDown
        self.customization.delete_all_widgets()

    def test_navigation_bar_widget(self):
        specify_wheel_diameter = self.project.activity(name='Specify wheel diameter')

        activities = [{
            'activityId': specify_wheel_diameter,
            'emphasize': True
            },
            {
            'activityId': self.widgets_test_task.id
            }]
        self.customization.add_navigation_bar_widget(activities=activities, alignment=NavigationBarAlignment.START)

        wrong_activities_because_unexpected_key = [{
            'activityId': specify_wheel_diameter,
            'emphasize': True
            },
            {
            'activityId': self.widgets_test_task.id,
            'whatIsThisKey': 'I have no idea'
            }]

        wrong_activities_because_activity_not_good = [{
            'activityId': 'This will fail',
            'emphasize': True
            }]
        with self.assertRaises(IllegalArgumentError):
            self.customization.add_navigation_bar_widget(activities=wrong_activities_because_unexpected_key)
        with self.assertRaises(IllegalArgumentError):
            self.customization.add_navigation_bar_widget(activities=wrong_activities_because_activity_not_good)

        widgets = self.customization.widgets()
        self.assertEqual(len(widgets), 1, "The customization should have 1 navigation bar widget")
        self.assertEqual(len(widgets[0]['config']['taskButtons']), 2, "The Widget should have 2 buttons")

        # tearDown
        self.customization.delete_all_widgets()

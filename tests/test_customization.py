from pykechain.models.customization import ExtCustomization
from tests.classes import TestBetamax


class TestExtCustomization(TestBetamax):
    """ Test the customization of activities """

    def setUp(self):
        super(TestExtCustomization, self).setUp()

        self.widgets_test_task = self.project.activity(name='Task to test all widgets')
        self.customization = self.widgets_test_task.customization()
        self.models, self.instances = self.widgets_test_task.associated_parts()

    def tearDown(self):
        super(TestExtCustomization, self).tearDown()
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

    def test_add_json_widget(self):
        """
        Test if a Json Widget can be added to the customization
        """
        self.customization.add_json_widget(dict(xtype="displayfield", value="Some text"))

        self.assertEqual(len(self.customization.widgets()), 1, "The customization should have 1 widget")
        self.assertTrue(self.customization.widgets()[0]["name"] == "jsonWidget",
                        "The first widget should be a jsonWidget")

    def test_add_property_grid_widget(self):
        """
        Test if a Property Grid Widget can be added to the customization
        """
        self.customization.add_property_grid_widget(self.instances[0])

        self.assertEqual(len(self.customization.widgets()), 1, "The customization should have 1 widget")
        self.assertTrue(self.customization.widgets()[0]["name"] == "propertyGridWidget",
                        "The first widget should be a propertyGridWidget")

    def test_add_property_grid_widget_with_max_height(self):
        """
        Test if a Property Grid Widget can be added to the customization with a max height
        """
        self.customization.add_property_grid_widget(self.instances[0], 20)

        self.assertEqual(len(self.customization.widgets()), 1, "The customization should have 1 widget")
        self.assertTrue(self.customization.widgets()[0]["name"] == "propertyGridWidget",
                        "The first widget should be a propertyGridWidget")
        self.assertEqual(self.customization.widgets()[0]["config"]["maxHeight"], 20,
                         "The max height property of the config should be 20")

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

    def test_add_property_grid_widget_with_no_title(self):
        """
        Test if a Property Grid Widget can be added to the customization without a title
        """
        self.customization.add_property_grid_widget(self.instances[0], None, False)

        self.assertEqual(len(self.customization.widgets()), 1, "The customization should have 1 widget")
        self.assertTrue(self.customization.widgets()[0]["name"] == "propertyGridWidget",
                        "The first widget should be a propertyGridWidget")
        self.assertEqual(self.customization.widgets()[0]["config"]["title"], None,
                         "The config should be not have a title property")

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

    def test_raise_error_when_delete_a_widget_of_empty_customization(self):
        """
        Test if an error is raised when trying to delete a widget when there are no widgets customized
        """
        self.assertEqual(len(self.customization.widgets()), 0, "The customization should have no widgets")

        with self.assertRaises(ValueError):
            self.customization.delete_widget(0)

    def test_delete_all_widgets(self):
        """
        Test if all widgets can be deleted
        """
        self.customization.add_property_grid_widget(self.instances[0])
        self.customization.add_property_grid_widget(self.instances[1])

        self.assertEqual(len(self.customization.widgets()), 2, "The customization should have 2 widget")

        self.customization.delete_all_widgets()

        self.assertEqual(len(self.customization.widgets()), 0, "The customization should have no widgets")

    def test_add_text_widget(self):
        """
        Test if a Text Widget can be added
        """
        self.customization.add_text_widget(text='This widget has text', custom_title='This widget also has title',
                                           collapsible=True)
        self.customization.add_text_widget()
        widgets = self.customization.widgets()
        self.assertEqual(len(widgets), 2, "The customization should have 2 widgets")
        self.assertTrue(widgets[0]['name'] == 'htmlWidget')
        self.assertTrue(widgets[0]['config']['html'] == 'This widget has text')
        self.assertTrue(widgets[0]['config']['title'] == 'This widget also has title')
        self.assertTrue(widgets[0]['config']['collapsible'])

        self.assertFalse('html' in widgets[1]['config'].keys())
        self.assertFalse(widgets[1]['config']['title'])
        self.assertFalse(widgets[1]['config']['collapsible'])
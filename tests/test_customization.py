from pykechain.models.customization import ExtCustomization
from tests.classes import TestBetamax


class TestExtCustomization(TestBetamax):
    """ Test the customization of activities """

    def setUp(self):
        super(TestExtCustomization, self).setUp()

        self.activity_1 = self.project.activity('Specify wheel diameter')  # Non customized
        self.activity_2 = self.project.activity('Customized task')  # Customized

    def test_get_customization_of_non_customized_task(self):
        """
        Test if an activity has a customization
        """
        customization = self.activity_1.customization()

        self.assertIsInstance(customization, ExtCustomization,
                              "The activity customization should be an instance of 'ExtCustomization'")
        self.assertTrue(hasattr(customization, "activity"), "The customization object should have a activity")
        self.assertEqual(customization.activity.id, self.activity_1.id, "The activity id of the customization object "
                                                                        "should be the same as the id of the activity")
        self.assertTrue(len(customization.widgets()) == 0, "The customizations should have no widgets")

    def test_add_json_widget(self):
        """
        Test if a Json Widget can be added to the customization
        """
        customization = self.activity_1.customization()

        customization.add_json_widget(dict(xtype="displayfield", value="Some text"))

        self.assertEqual(len(customization.widgets()), 1, "The customization should have 1 widget")
        self.assertTrue(customization.widgets()[0]["name"] == "jsonWidget",
                        "The first widget should be a jsonWidget")

        # Teardown
        customization.delete_all_widgets()

    def test_add_property_grid_widget(self):
        """
        Test if a Property Grid Widget can be added to the customization
        """
        customization = self.activity_1.customization()
        part = self.activity_1.parts()[0]

        customization.add_property_grid_widget(part)

        self.assertEqual(len(customization.widgets()), 1, "The customization should have 1 widget")
        self.assertTrue(customization.widgets()[0]["name"] == "propertyGridWidget",
                        "The first widget should be a propertyGridWidget")

        # Teardown
        customization.delete_all_widgets()

    def test_add_property_grid_widget_with_max_height(self):
        """
        Test if a Property Grid Widget can be added to the customization with a max height
        """
        customization = self.activity_1.customization()
        part = self.activity_1.parts()[0]

        customization.add_property_grid_widget(part, 20)

        self.assertEqual(len(customization.widgets()), 1, "The customization should have 1 widget")
        self.assertTrue(customization.widgets()[0]["name"] == "propertyGridWidget",
                        "The first widget should be a propertyGridWidget")
        self.assertEqual(customization.widgets()[0]["config"]["maxHeight"], 20,
                      "The max height property of the config should be 20")

        # Teardown
        customization.delete_all_widgets()

    def test_add_property_grid_widget_with_custom_title(self):
        """
        Test if a Property Grid Widget can be added to the customization with a custom title
        """
        customization = self.activity_1.customization()
        part = self.activity_1.parts()[0]
        custom_title = "my title"

        customization.add_property_grid_widget(part, None, custom_title)

        self.assertEqual(len(customization.widgets()), 1, "The customization should have 1 widget")
        self.assertTrue(customization.widgets()[0]["name"] == "propertyGridWidget",
                        "The first widget should be a propertyGridWidget")
        self.assertTrue(customization.widgets()[0]["config"]["title"] == custom_title,
                        "The title property of the config should be {}".format(custom_title))

        # Teardown
        customization.delete_all_widgets()

    def test_add_property_grid_widget_with_no_title(self):
        """
        Test if a Property Grid Widget can be added to the customization without a title
        """
        customization = self.activity_1.customization()
        part = self.activity_1.parts()[0]

        customization.add_property_grid_widget(part, None, False)

        self.assertEqual(len(customization.widgets()), 1, "The customization should have 1 widget")
        self.assertTrue(customization.widgets()[0]["name"] == "propertyGridWidget",
                        "The first widget should be a propertyGridWidget")
        self.assertEqual(customization.widgets()[0]["config"]["title"], None,
                      "The config should be not have a title property")

        # Teardown
        customization.delete_all_widgets()

    def test_delete_a_widget(self):
        """
        Test if a widget can be deleted by index
        """
        customization = self.activity_2.customization()
        part = self.activity_1.parts()[0]

        customization.add_property_grid_widget(part)

        self.assertEqual(len(customization.widgets()), 2, "The customization should have 2 widget")
        self.assertTrue(customization.widgets()[1]["name"] == "propertyGridWidget",
                        "The second widget should be a propertyGridWidget")

        customization.delete_widget(1)

        self.assertEqual(len(customization.widgets()), 1, "The customization should have 1 widget")
        self.assertTrue(customization.widgets()[0]["name"] == "jsonWidget",
                        "The first widget should be a jsonWidget")

    def test_raise_error_when_delete_a_widget_of_empty_customization(self):
        """
        Test if an error is raised when trying to delete a widget when there are no widgets customized
        """
        customization = self.activity_1.customization()

        self.assertEqual(len(customization.widgets()), 0, "The customization should have no widgets")

        with self.assertRaises(ValueError):
            customization.delete_widget(0)

    def test_delete_all_widgets(self):
        """
        Test if all widgets can be deleted
        """
        customization = self.activity_2.customization()
        part = self.activity_2.parts()[0]

        customization.add_property_grid_widget(part)

        self.assertEqual(len(customization.widgets()), 2, "The customization should have 2 widget")
        self.assertTrue(customization.widgets()[1]["name"] == "propertyGridWidget",
                        "The second widget should be a propertyGridWidget")

        customization.delete_all_widgets()

        self.assertEqual(len(customization.widgets()), 0, "The customization should have no widgets")

        # Teardown
        customization.add_json_widget(dict(xtype="displayfield", value="This is a custom widget!"))

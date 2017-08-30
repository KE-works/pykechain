from pykechain.models.customization import ExtCustomization
from tests.classes import TestBetamax


class TestExtCustomization(TestBetamax):
    """ Test the customization of activities """

    def setUp(self):
        super(TestExtCustomization, self).setUp()

        self.activity_1 = self.project.activity('Specify wheel diameter')  # Non customized

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

        # customization.add_json_widget(dict(xtype="displayfield", value="Some text"))
        #
        # self.assertIs(len(customization.widgets()), 1, "The customization should have 1 widget")
        # self.assertIs(customization.widgets()[0]["name"], "jsonWidget",
        #               "The first widget should be a jsonWidget")

        # Teardown
        customization.delete_all_widgets()

    def test_add_property_grid_widget(self):
        """
        Test if a Property Grid Widget can be added to the customization
        """
        customization = self.activity_1.customization()
        part = self.activity_1.parts()[0]

        customization.add_property_grid_widget(part)

        self.assertIs(len(customization.widgets()), 1, "The customization should have 1 widget")
        self.assertTrue(customization.widgets()[0]["name"] == "propertyGridWidget",
                      "The first widget should be a propertyGridWidget")

        # Teardown
        customization.delete_all_widgets()

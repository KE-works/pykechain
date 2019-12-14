from pykechain.exceptions import NotFoundError, IllegalArgumentError, APIError
from tests.classes import TestBetamax


class TestPartsReorderProperties(TestBetamax):
    # new in 1.10
    def test_reorder_properties_using_names(self):
        # Retrieve the front fork model
        front_fork_model = self.project.model('Front Fork')

        # Sort the properties of the front fork model based on their original order
        original_sorted_list_of_props = sorted(front_fork_model.properties, key=lambda k: k._json_data['order'])

        # Make a new list with only the names of the properties sorted by order. This will later be used to
        # reverse the order to the initial status
        original_list_of_prop_names = [prop.name for prop in original_sorted_list_of_props]

        # Instantiate the list that will be used to reorder the properties
        desired_order_list = ['Material', 'Height', 'Color']

        # Make the call to re-order the properties according to the above list
        front_fork_model.order_properties(property_list=desired_order_list)

        # Re-retrieve the front fork model
        front_fork_model = self.project.model('Front Fork')

        # Do the same steps as above. This will be used to check whether the action performed correctly.
        new_sorted_list_of_props = sorted(front_fork_model.properties, key=lambda k: k._json_data['order'])
        new_list_of_prop_names = [prop.name for prop in new_sorted_list_of_props]

        # Check the new list with the desired one
        self.assertEqual(desired_order_list, new_list_of_prop_names)

        # Return the front fork model to the initial status
        front_fork_model.order_properties(property_list=original_list_of_prop_names)

    def test_reorder_properties_using_objects(self):
        # Retrieve the front fork model
        front_fork_model = self.project.model('Front Fork')

        # Sort the properties of the front fork model based on their original order
        original_sorted_list_of_props = sorted(front_fork_model.properties, key=lambda k: k._json_data['order'])

        # Instantiate the list that will be used to reorder the properties
        desired_order_list = [front_fork_model.property('Material'),
                              front_fork_model.property('Height'),
                              front_fork_model.property('Color')]

        # Make the call to re-order the properties according to the above list
        front_fork_model.order_properties(property_list=desired_order_list)

        # Re-retrieve the front fork model
        front_fork_model = self.project.model('Front Fork')

        # Create a list of property id's, after the properties have been sorted.
        # This will be used to check whether the action performed correctly.
        new_sorted_list_of_props = sorted(front_fork_model.properties, key=lambda k: k._json_data['order'])
        new_list_of_prop_ids = [prop.id for prop in new_sorted_list_of_props]

        # Create a list of property id's, based on the desired order.
        desired_order_list_ids = [prop.id for prop in desired_order_list]

        # Check the new list with the desired one
        self.assertEqual(desired_order_list_ids, new_list_of_prop_ids)

        # Return the front fork model to the initial status
        front_fork_model.order_properties(property_list=original_sorted_list_of_props)

    def test_reorder_wrong_properties(self):
        # Retrieve the front fork model
        front_fork_model = self.project.model('Front Fork')

        # Instantiate a wrong list that will be used to reorder the properties.
        desired_order_list = ['Material', 'Height', 'Color', 'Width (mm)']

        with self.assertRaises(NotFoundError):
            front_fork_model.order_properties(property_list=desired_order_list)

    def test_reorder_not_list(self):
        # Retrieve the front fork model
        front_fork_model = self.project.model('Front Fork')

        # Instantiate a wrong list that will be used to reorder the properties.
        desired_order_list = 'Material Height Color'

        with self.assertRaises(IllegalArgumentError):
            front_fork_model.order_properties(property_list=desired_order_list)

    def test_reorder_properties_of_instance(self):
        # Retrieve the front fork model
        front_fork_instance = self.project.part(name='Front Fork', category='INSTANCE')

        # Instantiate a list that will be used to reorder the properties.
        desired_order_list = ['Material', 'Height', 'Color']

        with self.assertRaises(APIError):
            front_fork_instance.order_properties(property_list=desired_order_list)

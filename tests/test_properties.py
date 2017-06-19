from pykechain.exceptions import NotFoundError, APIError
from pykechain.models import Property
from tests.classes import TestBetamax


class TestProperties(TestBetamax):
    def test_retrieve_properties(self):
        properties = self.client.properties('Diameter')

        assert len(properties)

    def test_get_property(self):
        bike = self.project.part('Bike')

        self.assertEqual(bike.property('Gears').value, 10)

    def test_get_invalid_property(self):
        bike = self.project.part('Bike')

        with self.assertRaises(NotFoundError):
            bike.property('Price')

    def test_set_property(self):
        gears = self.project.part('Bike').property('Gears')

        gears.value = 5

        self.assertEqual(gears.value, 5)

        gears.value = 2

        self.assertEqual(self.project.part('Bike').property('Gears').value, 2)

        gears.value = 10

    def test_property_to_part(self):
        bike = self.project.part('Bike')

        bike2 = bike.property('Gears').part

        self.assertEqual(bike.id, bike2.id)

    def test_create_and_delete_property_model(self):
        # Retrieve the bike model
        bike = self.project.model('Bike')

        # test creation of new property model of bike
        new_property = bike.add_property(name='New property', property_type='CHAR',
                                         default_value='EUREKA!')

        # check whether the property has been created and whether it's name and type are correct
        self.assertIsInstance(bike.property('New property'), Property)
        self.assertEqual(bike.property('New property').value, 'EUREKA!')
        self.assertEqual(bike.property('New property')._json_data['property_type'], 'CHAR_VALUE')

        # Now delete the property model
        new_property.delete()

        # Retrieve the bike model again
        updated_bike = self.project.model('Bike')

        # Check whether it still has the property model that has just been deleted
        with self.assertRaises(NotFoundError):
            updated_bike.property('New property')

    def test_wrongly_creation_of_property(self):
        # These actions should not be possible. This test is of course, expecting APIErrors to be raised
        bike_model = self.project.model('Bike')

        # Test whether an integer property model can be created with an incorrect default value
        with self.assertRaises(APIError):
            bike_model.add_property(name='Integer', property_type='INT', default_value='Why is there a string here?')

    # 1.7.2
    def test_get_partmodel_of_propertymodel(self):
        """As found by @joost.schut, see #119 - thanks!"""

        wheel_model = self.project.model('Wheel')
        spokes_model = wheel_model.property('Spokes')
        part_of_spokes_model = spokes_model.part

        self.assertTrue(wheel_model.id == part_of_spokes_model.id)

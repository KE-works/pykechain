from random import randrange

from pykechain.exceptions import NotFoundError, APIError, IllegalArgumentError
from pykechain.models import Property
from tests.classes import TestBetamax


class TestProperties(TestBetamax):
    def test_retrieve_properties(self):
        properties = self.client.properties('Diameter')

        self.assertTrue(len(properties) > 0)

    def test_get_property_by_name(self):
        bike = self.project.part('Bike')
        # retrieve the property Gears directly via an API call
        gears_property = self.project._client.properties(name='Gears', category='INSTANCE')[0]

        self.assertEqual(bike.property('Gears'), gears_property)

    def test_get_property_by_uuid(self):
        bike = self.project.part('Bike')
        gears_id = bike.property('Gears').id
        # retrieve the property Gears directly via an API call
        gears_property = self.project._client.properties(name='Gears', category='INSTANCE')[0]

        self.assertEqual(bike.property(gears_id), gears_property)

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
        new_property = self.client.create_property(model=bike, name='New property', description='Nice prop',
                                                   property_type='CHAR', default_value='EUREKA!')

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

    # 1.11
    def test_edit_property_model_name(self):
        bike_model = self.project.model('Bike')
        gears_property = bike_model.property(name='Gears')
        gears_old_name = gears_property.name
        gears_property.edit(name='Cogs')
        gears_property_u = bike_model.property(name='Cogs')

        self.assertEqual(gears_property.id, gears_property_u.id)
        self.assertEqual(gears_property.name, gears_property_u.name)
        self.assertEqual(gears_property.name, 'Cogs')

        with self.assertRaises(IllegalArgumentError):
            gears_property.edit(name=True)
        # teardown
        gears_property.edit(name=gears_old_name)

    def test_edit_property_model_description(self):
        bike_model = self.project.model('Bike')
        gears_property = bike_model.property(name='Gears')
        gears_old_description = str(gears_property._json_data.get('description'))

        new_description = 'Cogs, definitely cogs.'
        gears_property.edit(description=new_description)
        gears_property_u = bike_model.property(name='Gears')

        self.assertEqual(gears_property.id, gears_property_u.id)
        with self.assertRaises(IllegalArgumentError):
            gears_property.edit(description=True)

        # teardown
        gears_property.edit(description=gears_old_description)

    def test_edit_property_model_unit(self):
        front_fork_model = self.project.model('Front Fork')
        height_property = front_fork_model.property(name='Height (mm)')
        height_old_unit = str(height_property._json_data.get('unit'))
        new_unit = 'm'

        height_property.edit(unit=new_unit)

        height_property_u = front_fork_model.property(name='Height (mm)')
        self.assertEqual(height_property.id, height_property_u.id)

        with self.assertRaises(IllegalArgumentError):
            height_property.edit(unit=4)

        # teardown
        height_property.edit(unit=height_old_unit)

    # 1.11
    def test_set_property_for_real(self):
        gears = self.project.part('Bike').property('Gears')
        old_value = int(gears.value)

        # set the value
        new_value = old_value * 20 + 1
        self.assertNotEqual(new_value, old_value)

        gears.value = new_value
        self.assertEqual(gears.value, new_value)
        self.assertEqual(gears._value, new_value)
        self.assertEqual(gears._json_data.get('value'), new_value)

        # teardown
        gears.value = old_value

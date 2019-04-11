from random import randrange

from pykechain.exceptions import NotFoundError, APIError, IllegalArgumentError
from pykechain.models import Property
from pykechain.enums import PropertyType
from tests.classes import TestBetamax


class TestProperties(TestBetamax):
    def test_retrieve_properties(self):
        properties = self.client.properties('Diameter')

        self.assertTrue(len(properties) > 0)

    def test_retrieve_properties_with_kwargs(self):
        # setUp
        bike = self.client.part(name='Bike')
        properties_with_kwargs = self.client.properties(part_id=bike.id)

        self.assertTrue(properties_with_kwargs)

        # testing
        for prop in properties_with_kwargs:
            self.assertEqual(prop.part.id, bike.id)

    def test_retrieve_property(self):
        prop = self.client.property(name='Test retrieve one property')

        self.assertTrue(prop)

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
                                                   property_type=PropertyType.CHAR_VALUE, default_value='EUREKA!')

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

    def test_create_property_where_model_is_instance(self):
        # setUp
        bike_instance = self.project.part(name='Bike')

        # testing
        with self.assertRaises(IllegalArgumentError):
            self.client.create_property(name='Properties are created on models only', model=bike_instance)

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
        height_property = front_fork_model.property(name='Height')
        height_old_unit = str(height_property._json_data.get('unit'))
        new_unit = 'm'

        height_property.edit(unit=new_unit)

        height_property_u = front_fork_model.property(name='Height')
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

    # 1.16
    def test_creation_of_all_property_model_types(self):
        # set up
        bike_model = self.project.model(name='Bike')

        # create a property model for each property type
        no_value_property_type = bike_model.add_property(name='Not correct property type', property_type='CHAR')
        no_property_type_specified = bike_model.add_property(name='No property type specified')
        single_line_text = bike_model.add_property(name='Single line text', property_type=PropertyType.CHAR_VALUE)
        multi_line_text = bike_model.add_property(name='Multi line text', property_type=PropertyType.TEXT_VALUE)
        integer = bike_model.add_property(name='Integer', property_type=PropertyType.INT_VALUE)
        decimal = bike_model.add_property(name='Float', property_type=PropertyType.FLOAT_VALUE)
        boolean = bike_model.add_property(name='Boolean', property_type=PropertyType.BOOLEAN_VALUE)
        datetime = bike_model.add_property(name='Datetime', property_type=PropertyType.DATETIME_VALUE)
        attachment = bike_model.add_property(name='Attachment', property_type=PropertyType.ATTACHMENT_VALUE)
        link = bike_model.add_property(name='Link', property_type=PropertyType.LINK_VALUE)
        single_select = bike_model.add_property(name='Single select', property_type=PropertyType.SINGLE_SELECT_VALUE)
        reference = bike_model.add_property(name='Reference', property_type=PropertyType.REFERENCES_VALUE)

        # teardown
        no_value_property_type.delete()
        no_property_type_specified.delete()
        single_line_text.delete()
        multi_line_text.delete()
        integer.delete()
        decimal.delete()
        boolean.delete()
        datetime.delete()
        attachment.delete()
        link.delete()
        single_select.delete()
        reference.delete()

    # 2.5.4
    def test_property_type_property(self):
        # set up
        front_fork_model = self.project.model('Front Fork')
        height_property = front_fork_model.property(name='Height')

        self.assertEqual(str(height_property.type), PropertyType.FLOAT_VALUE)

    def test_property_unit_property(self):
        # set up
        front_fork_model = self.project.model('Front Fork')
        height_property = front_fork_model.property(name='Height')

        self.assertEqual(str(height_property.unit), str(height_property._json_data.get('unit')))

    def test_property_description_property(self):
        # set up
        front_fork_model = self.project.model('Front Fork')
        height_property = front_fork_model.property(name='Height')

        self.assertEqual(str(height_property.description), str(height_property._json_data.get('description')))


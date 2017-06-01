from pykechain.exceptions import NotFoundError
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

    def test_create_and_delete_property(self):
        bike = self.project.model('Bike')

        new_property = self.client.create_property(model=bike, name='New property', property_type='CHAR',
                                                    default_value='EUREKA!')

        new_property.delete()

    # 1.7.2
    def test_get_partmodel_of_propertymodel(self):
        """As found by @joost.schut, see #119 - thanks!"""

        wheel_model = self.project.model('Wheel')
        spokes_model = wheel_model.property('Spokes')
        part_of_spokes_model = spokes_model.part

        self.assertTrue(wheel_model.id == part_of_spokes_model.id)

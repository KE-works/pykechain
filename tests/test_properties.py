from pykechain.exceptions import NotFoundError
from tests.classes import TestBetamax


class TestProperties(TestBetamax):

    def test_retrieve_properties(self):
        properties = self.client.properties('Diameter')

        assert len(properties)

    def test_get_property(self):
        project = self.client.scope('Bike Project')
        bike = project.part('Bike')

        self.assertEqual(bike.property('Gears').value, 6)

    def test_get_invalid_property(self):
        project = self.client.scope('Bike Project')
        bike = project.part('Bike')

        with self.assertRaises(NotFoundError):
            bike.property('Price')

    def test_set_property(self):
        project = self.client.scope('Bike Project')
        gears = project.part('Bike').property('Gears')

        gears.value = 10

        self.assertEqual(gears.value, 10)

    def test_property_to_part(self):
        project = self.client.scope('Bike Project')
        bike = project.part('Bike')\

        bike2 = bike.property('Gears').part

        self.assertEqual(bike.id, bike2.id)

from pykechain.exceptions import NotFoundError
from tests.classes import TestBetamax


class TestProperties(TestBetamax):
    def test_retrieve_properties(self):
        properties = self.client.properties('Float')

        assert len(properties)

    def test_get_property(self):
        bike = self.project.part('One')

        self.assertEqual(bike.property('Integer').value, 10)

    def test_get_invalid_property(self):
        bike = self.project.part('One')

        with self.assertRaises(NotFoundError):
            bike.property('Price')

    def test_set_property(self):
        int = self.project.part('One').property('Integer')

        int.value = 5

        self.assertEqual(int.value, 5)

        int.value = 2

        self.assertEqual(self.project.part('One').property('Integer').value, 2)

        int.value = 10

    def test_property_to_part(self):
        bike = self.project.part('One')

        bike2 = bike.property('Float').part

        self.assertEqual(bike.id, bike2.id)

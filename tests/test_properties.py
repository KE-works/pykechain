from pykechain.exceptions import NotFoundError
from tests.classes import TestBetamax


class TestProperties(TestBetamax):
    def test_retrieve_properties(self):
        properties = self.client.properties('Float')

        assert len(properties)

    def test_get_property(self):
        one = self.project.part('One')

        self.assertEqual(one.property('Integer').value, 10)

    def test_get_invalid_property(self):
        one = self.project.part('One')

        with self.assertRaises(NotFoundError):
            one.property('Price')

    def test_set_property(self):
        int = self.project.part('One').property('Integer')

        int.value = 5

        self.assertEqual(int.value, 5)

        int.value = 2

        self.assertEqual(self.project.part('One').property('Integer').value, 2)

        int.value = 10

    def test_property_to_part(self):
        one = self.project.part('One')
        one2 = one.property('Float').part

        self.assertEqual(one.id, one2.id)

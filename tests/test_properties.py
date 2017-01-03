from tests.classes import TestBetamax


class TestProperties(TestBetamax):

    def test_retrieve_properties(self):
        properties = self.client.properties('Diameter')

        assert len(properties)

    def test_get_property(self):
        project = self.client.scope('Bike Project')
        bike = project.part('Bike')

        self.assertEqual(bike.property('Gears').value, 6)

    def test_set_property(self):
        project = self.client.scope('Bike Project')
        gears = project.part('Bike').property('Gears')

        gears.value = 10

        self.assertEqual(gears.value, 10)


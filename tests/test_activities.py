from pykechain.exceptions import NotFoundError, MultipleFoundError
from tests.classes import TestBetamax


class TestActivities(TestBetamax):

    def test_retrieve_activities(self):
        assert self.client.activities()

    def test_retrieve_single_activity(self):
        assert self.client.activity('Specify wheel diameter')

    def test_retrieve_unknown_activity(self):
        with self.assertRaises(NotFoundError):
            self.client.activity('Hello?!')

    def test_retrieve_too_many_activity(self):
        with self.assertRaises(MultipleFoundError):
            self.client.activity('Lorem ipsum')

    def test_retrieve_single_bike(self):
        activity = self.client.activity('See whole bike')

        parts = activity.parts()

        assert len(parts) == 1

        bike = parts[0]

        assert len(bike.properties) == 1

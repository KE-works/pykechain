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
            self.client.activity()

    def test_retrieve_single_bike(self):
        activity = self.client.activity('Specify wheel diameter')

        parts = activity.parts()

        assert len(parts) == 2

    def test_create_activity(self):
        project = self.client.scope('Bike Project')

        task = project.create_activity('Random')

        assert task.name == 'Random'

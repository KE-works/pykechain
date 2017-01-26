from pykechain.exceptions import NotFoundError, MultipleFoundError, APIError
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

        subprocess = project.create_activity('Random', activity_class='Subprocess')

        assert subprocess.name == 'Random'

        task = subprocess.create_activity('Another')

        subprocess.delete()

        with self.assertRaises(APIError):
            subprocess.delete()

    def test_configure_activity(self):
        project = self.client.scope('Bike Project')

        bike = project.model('Bike')
        wheel = project.model('Wheel')

        task = project.create_activity('Random')

        task.configure([
            bike.property('Gears'),
            bike.property('Total height')
        ], [
            wheel.property('Spokes')
        ])

        task.delete()
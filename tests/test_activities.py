from pykechain.exceptions import NotFoundError, MultipleFoundError, APIError
from tests.classes import TestBetamax


class TestActivities(TestBetamax):
    def test_retrieve_activities(self):
        assert self.project.activities()

    def test_retrieve_single_activity(self):
        assert self.project.activity('Task')

    def test_retrieve_unknown_activity(self):
        with self.assertRaises(NotFoundError):
            self.project.activity('task-does-not-exist')

    def test_retrieve_too_many_activity(self):
        with self.assertRaises(MultipleFoundError):
            self.project.activity()

    def test_retrieve_activity_parts(self):
        activity = self.project.activity('Task2')

        parts = activity.parts()

        assert len(parts) == 2

    def test_create_activity(self):
        subprocess = self.project.create_activity('Subprocess', activity_class='Subprocess')

        assert subprocess.name == 'Subprocess'

        task = subprocess.create_activity('Subtask')

        subprocess.delete()

        with self.assertRaises(APIError):
            task.delete()

    def test_configure_activity(self):
        one = self.project.model('One')
        many = self.project.model('Many')

        task = self.project.create_activity('TestTask')

        task.configure([
            one.property('Integer'),
            one.property('Boolean')
        ], [
            many.property('Float')
        ])

        task.delete()

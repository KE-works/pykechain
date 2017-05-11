from pykechain.exceptions import NotFoundError, MultipleFoundError, APIError
from tests.classes import TestBetamax
import datetime
from datetime import timezone

class TestActivities(TestBetamax):
    def test_retrieve_activities(self):
        assert self.project.activities()

    def test_retrieve_single_activity(self):
        assert self.project.activity('Specify wheel diameter')

    def test_retrieve_unknown_activity(self):
        with self.assertRaises(NotFoundError):
            self.project.activity('Hello?!')

    def test_retrieve_too_many_activity(self):
        with self.assertRaises(MultipleFoundError):
            self.project.activity()

    def test_retrieve_single_bike(self):
        activity = self.project.activity('Specify wheel diameter')

        parts = activity.parts()

        assert len(parts) == 2

    def test_create_activity(self):
        project = self.project

        subprocess = project.create_activity('Random', activity_class='Subprocess')

        assert subprocess.name == 'Random'

        task = subprocess.create_activity('Another')

        subprocess.delete()

        with self.assertRaises(APIError):
            subprocess.delete()

    def test_configure_activity(self):
        project = self.project

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

    def test_edit_activity_name(self):
        specify_wd = self.project.activity('Specify wheel diameter')
        specify_wd.edit(name='Specify wheel diameter - updated')

        specify_wd_u = self.project.activity('Specify wheel diameter - updated')
        assert specify_wd.id == specify_wd_u.id
        assert specify_wd.name == specify_wd_u.name
        assert specify_wd.name == 'Specify wheel diameter - updated'

        specify_wd.edit(name='Specify wheel diameter')

    def test_edit_activity_description(self):
        specify_wd = self.project.activity('Specify wheel diameter')
        specify_wd.edit(description='This task has an even cooler description')

        specify_wd_u = self.project.activity('Specify wheel diameter')
        assert specify_wd.id == specify_wd_u.id

        specify_wd.edit(description='This task has a cool description')

    def test_edit_activity_dates(self):
        specify_wd = self.project.activity('Specify wheel diameter')
        start_time = datetime.datetime(2000,1,1,0,0,0)
        due_time = datetime.datetime(2019,12,31,0,0,0)

        specify_wd.edit(start_date=start_time, due_date=due_time)

        specify_wd_u = self.project.activity('Specify wheel diameter')

        assert specify_wd.id == specify_wd_u.id

        specify_wd.edit(start_date=datetime.datetime.today(), due_date=datetime.datetime.today())

    def test_edit_activity_assignee(self):
        specify_wd = self.project.activity('Specify wheel diameter')

        specify_wd.edit(assignee='pykechain')

        specify_wd_u = self.project.activity('Specify wheel diameter')

        assert specify_wd.id == specify_wd_u.id

        specify_wd.edit(assignee='testuser')

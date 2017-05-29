import warnings

import pytz
import requests
from datetime import datetime

from pykechain.exceptions import NotFoundError, MultipleFoundError, APIError
from tests.classes import TestBetamax

ISOFORMAT = "%Y-%m-%dT%H:%M:%SZ"


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

    # new in 1.7
    def test_edit_activity_name(self):
        specify_wd = self.project.activity('Specify wheel diameter')
        specify_wd.edit(name='Specify wheel diameter - updated')

        specify_wd_u = self.project.activity('Specify wheel diameter - updated')
        self.assertEqual(specify_wd.id, specify_wd_u.id)
        self.assertEqual(specify_wd.name, specify_wd_u.name)
        self.assertEqual(specify_wd.name, 'Specify wheel diameter - updated')

        # Added to improve coverage. Assert whether TypeError is raised when 'name' is not a string object.
        with self.assertRaises(TypeError):
            specify_wd.edit(name=True)

        specify_wd.edit(name='Specify wheel diameter')

    def test_edit_activity_description(self):
        specify_wd = self.project.activity('Specify wheel diameter')
        specify_wd.edit(description='This task has an even cooler description')

        self.assertEqual(specify_wd._client.last_response.status_code, requests.codes.ok)

        # Added to improve coverage. Assert whether TypeError is raised when 'description' is not a string object.
        with self.assertRaises(TypeError):
            specify_wd.edit(description=42)

        specify_wd.edit(description='This task has a cool description')

    def test_edit_activity_naive_dates(self):
        specify_wd = self.project.activity('Specify wheel diameter')

        old_start, old_due = datetime.strptime(specify_wd._json_data.get('start_date'), ISOFORMAT), \
                             datetime.strptime(specify_wd._json_data.get('due_date'), ISOFORMAT)
        start_time = datetime(2000, 1, 1, 0, 0, 0)
        due_time = datetime(2019, 12, 31, 0, 0, 0)

        with warnings.catch_warnings(record=False) as w:
            warnings.simplefilter("ignore")
            specify_wd.edit(start_date=start_time, due_date=due_time)

        self.assertEqual(specify_wd._client.last_response.status_code, requests.codes.ok)

        # Added to improve coverage. Assert whether TypeError is raised when 'start_date' and 'due_date are not
        # datetime objects
        with self.assertRaises(TypeError):
            specify_wd.edit(start_date='All you need is love')

        with self.assertRaises(TypeError):
            specify_wd.edit(due_date='Love is all you need')

        specify_wd_u = self.project.activity('Specify wheel diameter')

        assert specify_wd.id == specify_wd_u.id

        specify_wd.edit(start_date=old_start, due_date=old_due)

    def test_edit_due_date_timezone_aware(self):
        specify_wd = self.project.activity('Specify wheel diameter')

        # save old values
        old_start, old_due = datetime.strptime(specify_wd._json_data.get('start_date'), ISOFORMAT), \
                             datetime.strptime(specify_wd._json_data.get('due_date'), ISOFORMAT)

        startdate = datetime.now(pytz.utc)
        duedate = datetime(2019, 1, 1, 0, 0, 0, tzinfo=pytz.timezone('Europe/Amsterdam'))

        specify_wd.edit(start_date=startdate, due_date=duedate)

        self.assertEqual(specify_wd._client.last_response.status_code, requests.codes.ok)

        # teardown
        specify_wd.edit(start_date=old_start, due_date=old_due)

    def test_edit_activity_assignee(self):
        specify_wd = self.project.activity('Specify wheel diameter')
        original_assignee = specify_wd._json_data.get('assignee', 'testuser')

        specify_wd.edit(assignee='pykechain')

        self.assertEqual(specify_wd._client.last_response.status_code, requests.codes.ok)

        # Added to improve coverage. Assert whether NotFoundError is raised when 'assignee' is not part of the
        # scope members
        with self.assertRaises(NotFoundError):
            specify_wd.edit(assignee='Not Member')

        # Added to improve coverage. Assert whether NotFoundError is raised when 'assignee' is not part of the
        # scope members
        with self.assertRaises(TypeError):
            specify_wd.edit(assignee=0.5)

        specify_wd.edit(assignee=original_assignee)

    def test_customize_activity(self):
        activity_to_costumize = self.project.activity('Customized task')
        activity_to_costumize.customize(
        config={"components": [{
        "xtype": "superGrid",
        "filter": {
            "parent": "e5106946-40f7-4b49-ae5e-421450857911",
            "model": "edc8eba0-47c5-415d-8727-6d927543ee3b"}}]})
from datetime import datetime
from unittest import skip, skipIf

import pytz
import requests
import warnings
import os

from pykechain.enums import Category, ActivityType, ActivityStatus
from pykechain.exceptions import NotFoundError, MultipleFoundError, APIError, IllegalArgumentError
from pykechain.models import Part, Activity
from tests.classes import TestBetamax
from tests.utils import TEST_FLAG_IS_WIM2
from pykechain.utils import temp_chdir

ISOFORMAT = "%Y-%m-%dT%H:%M:%SZ"
ISOFORMAT_HIGHPRECISION = "%Y-%m-%dT%H:%M:%S.%fZ"


class TestActivities(TestBetamax):
    def test_retrieve_activities(self):
        self.assertTrue(self.project.activities())

    def test_retrieve_single_activity(self):
        self.assertTrue(self.project.activity('Specify wheel diameter'))

    def test_retrieve_unknown_activity(self):
        with self.assertRaises(NotFoundError):
            self.project.activity('Hello?!')

    def test_retrieve_too_many_activity(self):
        with self.assertRaises(MultipleFoundError):
            self.project.activity()

    def test_retrieve_single_bike(self):
        activity = self.project.activity('Specify wheel diameter')

        parts = activity.parts()

        self.assertEqual(len(parts), 2)

    def test_create_activity(self):
        # set up
        project = self.project

        subprocess = project.create_activity('Test subprocess creation', activity_type='PROCESS')
        self.assertEqual(subprocess.name, 'Test subprocess creation')

        task = subprocess.create('Test task creation')
        self.assertEqual(task.name, 'Test task creation')

        # teardown
        subprocess.delete()

        with self.assertRaises(NotFoundError):
            project.activity(name='Test subprocess creation')
        with self.assertRaises(NotFoundError):
            project.activity(name='Test task creation')

    def test_create_activity_under_task(self):
        task = self.project.activity('Specify wheel diameter')

        with self.assertRaises(IllegalArgumentError):
            task.create('This cannot happen')

    def test_configure_activity(self):
        # setup
        project = self.project

        bike = project.model('Bike')
        wheel = project.model('Wheel')

        task = project.create_activity('Test activity configuration')

        task.configure(
            inputs=[
                bike.property('Gears'),
                bike.property('Total height')
            ],
            outputs=[
                wheel.property('Spokes')
            ])

        associated_models, associated_instances = task.associated_parts()

        self.assertEqual(len(associated_models), 2)
        self.assertEqual(len(associated_instances), 3)

        # teardown
        task.delete()

    # new in 1.7
    def test_edit_activity_name(self):
        specify_wd = self.project.activity('Specify wheel diameter')
        specify_wd.edit(name='Specify wheel diameter - updated')

        specify_wd_u = self.project.activity('Specify wheel diameter - updated')
        self.assertEqual(specify_wd.id, specify_wd_u.id)
        self.assertEqual(specify_wd.name, specify_wd_u.name)
        self.assertEqual(specify_wd.name, 'Specify wheel diameter - updated')

        # Added to improve coverage. Assert whether IllegalArgumentError is raised when 'name' is not a string object.
        with self.assertRaises(IllegalArgumentError):
            specify_wd.edit(name=True)

        specify_wd.edit(name='Specify wheel diameter')

    def test_edit_activity_description(self):
        specify_wd = self.project.activity('Specify wheel diameter')
        specify_wd.edit(description='This task has an even cooler description')

        self.assertEqual(specify_wd._client.last_response.status_code, requests.codes.ok)

        # Added to improve coverage. Assert whether IllegalArgumentError is raised when 'description' is
        # not a string object.
        with self.assertRaises(IllegalArgumentError):
            specify_wd.edit(description=42)

        specify_wd.edit(description='This task has a cool description')

    def test_edit_activity_naive_dates(self):
        specify_wd = self.project.activity('Specify wheel diameter')

        old_start, old_due = self._convert_timestamp(specify_wd._json_data.get('start_date')), \
                             self._convert_timestamp(specify_wd._json_data.get('due_date'))
        start_time = datetime(2000, 1, 1, 0, 0, 0)
        due_time = datetime(2019, 12, 31, 0, 0, 0)

        with warnings.catch_warnings(record=False) as w:
            warnings.simplefilter("ignore")
            specify_wd.edit(start_date=start_time, due_date=due_time)

        self.assertEqual(specify_wd._client.last_response.status_code, requests.codes.ok)

        # Added to improve coverage. Assert whether IllegalArgumentError is raised when 'start_date' and
        # 'due_date are not datetime objects
        with self.assertRaises(IllegalArgumentError):
            specify_wd.edit(start_date='All you need is love')

        with self.assertRaises(IllegalArgumentError):
            specify_wd.edit(due_date='Love is all you need')

        specify_wd_u = self.project.activity('Specify wheel diameter')

        self.assertEqual(specify_wd.id, specify_wd_u.id)

        specify_wd.edit(start_date=old_start, due_date=old_due)

    def test_edit_due_date_timezone_aware(self):
        specify_wd = self.project.activity('Specify wheel diameter')

        # save old values
        old_start, old_due = self._convert_timestamp(specify_wd._json_data.get('start_date')), \
                             self._convert_timestamp(specify_wd._json_data.get('due_date'))

        startdate = datetime.now(pytz.utc)
        duedate = datetime(2019, 1, 1, 0, 0, 0, tzinfo=pytz.timezone('Europe/Amsterdam'))

        specify_wd.edit(start_date=startdate, due_date=duedate)

        self.assertEqual(specify_wd._client.last_response.status_code, requests.codes.ok)

        # teardown
        specify_wd.edit(start_date=old_start, due_date=old_due)

    # 1.10.0
    def test_edit_activity_status(self):
        specify_wd = self.project.activity('Specify wheel diameter')
        original_status = specify_wd.status

        specify_wd.edit(status=ActivityStatus.COMPLETED)

        # Added to improve coverage. Assert whether IllegalArgumentError is raised when 'status' is not a string
        with self.assertRaises(IllegalArgumentError):
            specify_wd.edit(status=True)

        # If the status is not part of Enums.Status then it should raise an APIError
        with self.assertRaises(IllegalArgumentError):
            specify_wd.edit(status='NO STATUS')

        # Return the status to how it used to be
        specify_wd.edit(status=original_status)

    def _convert_timestamp(self, value):
        try:
            r = datetime.strptime(value, ISOFORMAT)
        except ValueError:
            r = datetime.strptime(value, ISOFORMAT_HIGHPRECISION)
        if isinstance(r, datetime):
            return r
        else:
            raise ValueError

    # 1.7.2
    def test_datetime_with_naive_duedate_only_fails(self):
        """reference to #121 - thanks to @joost.schut"""
        # setup
        specify_wd = self.project.activity('Specify wheel diameter')

        # save old values
        old_start, old_due = self._convert_timestamp(specify_wd._json_data.get('start_date')), \
                             self._convert_timestamp(specify_wd._json_data.get('due_date'))
        naive_duedate = datetime(2017, 6, 5, 5, 0, 0)
        with warnings.catch_warnings(record=False) as w:
            warnings.simplefilter("ignore")
            specify_wd.edit(due_date=naive_duedate)

        # teardown
        with warnings.catch_warnings(record=False) as w:
            warnings.simplefilter("ignore")
            specify_wd.edit(due_date=old_due)

    def test_datetime_with_tzinfo_provides_correct_offset(self):
        """reference to #121 - thanks to @joost.schut

        The tzinfo.timezone('Europe/Amsterdam') should provide a 2 hour offset, recording 20 minutes
        """
        # setup
        specify_wd = self.project.activity('Specify wheel diameter')
        # save old values
        old_start, old_due = self._convert_timestamp(specify_wd._json_data.get('start_date')), \
                             self._convert_timestamp(specify_wd._json_data.get('due_date'))

        tz = pytz.timezone('Europe/Amsterdam')
        tzaware_due = tz.localize(datetime(2017, 7, 1))
        tzaware_start = tz.localize(datetime(2017, 6, 30, 0, 0, 0))

        specify_wd.edit(start_date=tzaware_start)
        self.assertTrue(specify_wd._json_data['start_date'], tzaware_start.isoformat(sep='T'))

        specify_wd.edit(due_date=tzaware_due)
        self.assertTrue(specify_wd._json_data['due_date'], tzaware_due.isoformat(sep='T'))

        # teardown
        with warnings.catch_warnings(record=False) as w:
            warnings.simplefilter("ignore")
            specify_wd.edit(start_date=old_start, due_date=old_due)

    def test_retrieve_children_of_task_fails_for_task(self):
        task = self.project.activity(name='Specify wheel diameter')
        with self.assertRaises(NotFoundError):
            task.children()

    def test_retrieve_activity_by_id(self):
        task = self.project.activity(name='Subprocess')  # type: Activity

        task_by_id = self.client.activity(pk=task.id)

        self.assertEqual(task.id, task_by_id.id)

    def test_retrieve_siblings_of_a_task_in_a_subprocess(self):
        task = self.project.activity(name='Subprocess')  # type: Activity
        siblings = task.siblings()

        self.assertTrue(task.id in [sibling.id for sibling in siblings])
        self.assertTrue(len(siblings) == 7)

    def test_retrieve_part_associated_to_activities(self):
        task = self.project.activity('Specify wheel diameter')
        parts = list(task.parts())

        for part in parts:
            self.assertIsInstance(part, Part)
            self.assertTrue(part.category == Category.INSTANCE)

    def test_retrieve_part_models_associated_to_activities(self):
        task = self.project.activity('Specify wheel diameter')
        models = list(task.parts(category=Category.MODEL))

        for model in models:
            self.assertIsInstance(model, Part)
            self.assertTrue(model.category == Category.MODEL)
            if model.name == 'Bike':
                self.assertTrue(not model.property('Gears').output)
            elif model.name == 'Front Fork':
                self.assertTrue(model.property('Material').output)

    def test_retrieve_associated_parts_to_activity(self):
        task = self.project.activity('Specify wheel diameter')
        (models, parts) = list(task.associated_parts())

        for part in models:
            self.assertIsInstance(part, Part)
            self.assertTrue(part.category == Category.MODEL)

        for part in parts:
            self.assertIsInstance(part, Part)
            self.assertTrue(part.category == Category.INSTANCE)

    # in 1.12

    def test_retrieve_siblings_of_a_task_in_a_subprocess_with_arguments(self):
        task = self.project.activity(name='SubTask')  # type: Activity
        siblings = task.siblings(name__icontains='sub')

        self.assertTrue(task.id in [sibling.id for sibling in siblings])
        self.assertTrue(len(siblings) == 2)

    # in 1.12.9
    def test_activity_without_scope_id_will_fix_itself(self):
        specify_wheel_diam_cripled = self.project.activity(name='Specify wheel diameter', fields='id,name,status')
        self.assertFalse(specify_wheel_diam_cripled.scope)

        # now the self-healing will beging
        self.assertEqual(specify_wheel_diam_cripled.scope_id, self.project.id)

    # in 1.13
    def test_create_activity_with_incorrect_activity_class_fails(self):
        with self.assertRaisesRegex(IllegalArgumentError, 'Please provide accepted activity_type'):
            self.project.create_activity(name='New', activity_type='DEFUNCTActivity')


class TestActivitiesCustomisation(TestBetamax):
    # updated and new in 1.9
    @skip('KE-chain deprecated the inspector components')
    def test_customize_activity_with_widget_config(self):
        # Retrieve the activity to be customized
        activity_to_costumize = self.project.activity('Customized task')

        # Create the widget config it should have now
        widget_config = {'components': [{'xtype': 'superGrid', 'filter':
            {'parent': 'e5106946-40f7-4b49-ae5e-421450857911',
             'model': 'edc8eba0-47c5-415d-8727-6d927543ee3b'}}]}

        # Customize it with a config
        activity_to_costumize.customize(
            config=widget_config)

        # Re-retrieve it
        activity_to_costumize = self.project.activity('Customized task')

        # Check whether it's widget config has changed
        self.assertTrue(activity_to_costumize._json_data['widget_config']['config'] != '{}')

        # Change it back to an empty config
        activity_to_costumize.customize(config={})

    @skip('KE-chain deprecated the inspector components')
    def test_customize_new_activity(self):
        # Create the activity to be freshly customized
        new_task = self.project.create_activity('New task')

        # Customize it with a config
        new_task.customize(
            config={"components": [{
                "xtype": "superGrid",
                "filter": {
                    "parent": "e5106946-40f7-4b49-ae5e-421450857911",
                    "model": "edc8eba0-47c5-415d-8727-6d927543ee3b"}}]})

        # Retrieve it again
        new_task = self.project.activity('New task')

        # Check whether it's widget config has changed
        self.assertTrue(new_task._json_data['widget_config']['config'] is not None)

        # Delete it
        new_task.delete()

    def test_wrong_customization(self):
        # Set up
        new_task = self.project.create_activity('Task for wrong customization')
        config = 'This will not work'

        with self.assertRaises(Exception):
            new_task.customize(config)

        # teardown
        new_task.delete()


@skipIf(TEST_FLAG_IS_WIM2, reason="This tests is designed for WIM version 1, expected to fail on newer WIM")
class TestActivity1SpecificTests(TestBetamax):
    def test_edit_activity1_assignee(self):
        specify_wd = self.project.activity('Specify wheel diameter')
        original_assignee = specify_wd._json_data.get('assignees', ['testuser', 'testmanager'])

        specify_wd.edit(assignees=['pykechain'])

        specify_wd.refresh()  # = self.project.activity('Specify wheel diameter')
        self.assertEqual(['pykechain'], specify_wd._json_data.get('assignees'))

        # Added to improve coverage. Assert whether NotFoundError is raised when 'assignee' is not part of the
        # scope members
        with self.assertRaises(NotFoundError):
            specify_wd.edit(assignees=['Not Member'])

        # Added to improve coverage. Assert whether NotFoundError is raised when 'assignee' is not part of the
        # scope members
        with self.assertRaises(IllegalArgumentError):
            specify_wd.edit(assignees='Not Member')

        specify_wd.edit(assignees=original_assignee)

    def test_root_activity1_is_root(self):
        specify_wd = self.project.activity('Specify wheel diameter')

        self.assertTrue(specify_wd.is_rootlevel())

    def test_subtask_activity1_is_not_root(self):
        subprocess_subtask = self.project.activity('SubTask')

        self.assertFalse(subprocess_subtask.is_rootlevel())
        self.assertTrue(subprocess_subtask.subprocess())

    def test_activity1_is_task(self):
        specify_wd = self.project.activity('Specify wheel diameter')

        self.assertTrue(specify_wd.is_task())
        self.assertFalse(specify_wd.is_subprocess())

    def test_activity1_is_subprocess(self):
        subprocess = self.project.activity('Subprocess')

        self.assertTrue(subprocess.is_subprocess())
        self.assertFalse(subprocess.is_task())

    def test_activity1_is_configured_not_customised(self):
        specify_wd = self.project.activity('Specify wheel diameter')

        self.assertTrue(specify_wd.is_configured())
        self.assertFalse(specify_wd.is_customized())

    def test_unconfigured_subtask_activity1_is_not_configured(self):
        subprocess_subtask = self.project.activity('SubTask')

        self.assertFalse(subprocess_subtask.is_configured())
        self.assertFalse(subprocess_subtask.is_customized())

    def test_activity1_is_configured_and_customised(self):
        customized_task = self.project.activity('Customized task')

        self.assertTrue(customized_task.is_configured())
        self.assertTrue(customized_task.is_customized())


@skipIf(not TEST_FLAG_IS_WIM2, reason="This tests is designed for WIM version 2, expected to fail on older WIM")
class TestActivity2SpecificTests(TestBetamax):
    # 2.0 new activity
    def test_edit_activity2_assignee(self):
        specify_wd = self.project.activity('Specify wheel diameter')  # type: Activity2
        original_assignee_ids = specify_wd._json_data.get('assignee_ids') or []

        # pykechain_user = self.client.user(username='pykechain')
        test_user = self.client.user(username='testuser')

        specify_wd.edit(assignees_ids=[test_user.id])
        specify_wd.refresh()

        self.assertEqual(['testuser'], specify_wd._json_data.get('assignees_names'))

        self.assertEqual(specify_wd._client.last_response.status_code, requests.codes.ok)

        # Added to improve coverage. Assert whether NotFoundError is raised when 'assignee' is not part of the
        # scope members
        with self.assertRaises(NotFoundError):
            specify_wd.edit(assignees_ids=[-100])

        # Added to improve coverage. Assert whether NotFoundError is raised when 'assignee' is not part of the
        # scope members
        with self.assertRaises(IllegalArgumentError):
            specify_wd.edit(assignees_ids='this should have been a list')

        specify_wd.edit(assignees_ids=original_assignee_ids)

    def test_activity2_retrieve_parent_of_task(self):
        task = self.project.activity(name='SubTask')
        subprocess = task.parent()  # type Activity
        self.assertEqual(subprocess.activity_type, ActivityType.PROCESS)

    def test_activity2_retrieve_parent_of_a_toplevel_task_returns_workflow_root_id(self):
        task = self.project.activity('Specify wheel diameter')
        parent = task.parent()
        self.assertEqual(self.project._json_data.get('workflow_root_id'), parent.id)

    def test_activity2_test_workflow_root_object(self):
        workflow_root = self.project.activity(id=self.project._json_data.get('workflow_root_id'))

        self.assertTrue(workflow_root.is_root())
        self.assertTrue(workflow_root.is_workflow_root())

    def test_activity2_retrieve_children_of_parent(self):
        subprocess = self.project.activity(name='Subprocess')  # type: Activity
        children = subprocess.children()
        self.assertTrue(len(children) >= 1)
        for child in children:
            self.assertEqual(child._json_data.get('parent_id'), subprocess.id)

    def test_activity2_retrieve_children_of_subprocess_with_arguments(self):
        subprocess = self.project.activity(name='Subprocess')  # type: Activity
        children = subprocess.children(name__icontains='task')
        self.assertTrue(len(children) >= 1)
        for child in children:
            self.assertEqual(child._json_data.get('parent_id'), subprocess.id)

    def test_rootlevel_activity2_is_rootlevel(self):
        specify_wd = self.project.activity('Specify wheel diameter')

        self.assertTrue(specify_wd.is_rootlevel())

    def test_subtask_activity2_is_not_rootlevel(self):
        subprocess_subtask = self.project.activity('SubTask')

        self.assertFalse(subprocess_subtask.is_rootlevel())
        self.assertTrue(subprocess_subtask.subprocess())

    def test_activity2_is_task(self):
        specify_wd = self.project.activity('Specify wheel diameter')

        self.assertTrue(specify_wd.is_task())
        self.assertFalse(specify_wd.is_subprocess())

    def test_activity2_is_subprocess(self):
        subprocess = self.project.activity('Subprocess')

        self.assertTrue(subprocess.is_subprocess())
        self.assertFalse(subprocess.is_task())

    def test_activity2_is_configured_not_customised(self):
        specify_wd = self.project.activity('Specify wheel diameter')

        self.assertTrue(specify_wd.is_configured())
        self.assertFalse(specify_wd.is_customized())

    def test_unconfigured_subtask_activity2_is_not_configured(self):
        subprocess_subtask = self.project.activity('SubTask')

        self.assertFalse(subprocess_subtask.is_configured())
        self.assertFalse(subprocess_subtask.is_customized())

    def test_activity2_is_configured_and_customised(self):
        customized_task = self.project.activity('Customized task')

        self.assertTrue(customized_task.is_configured())
        self.assertTrue(customized_task.is_customized())

    def test_activity2_download_as_pdf(self):
        # setUp
        activity_name = 'Demo - PDF exporting'
        activity = self.project.activity(name=activity_name)

        # testing
        with temp_chdir() as target_dir:
            activity.download_as_pdf(target_dir=target_dir, pdf_filename='pdf_file')
            activity.download_as_pdf(target_dir=target_dir)
            pdf_file = os.path.join(target_dir, 'pdf_file.pdf')
            pdf_file_called_after_activity = os.path.join(target_dir, activity_name + '.pdf')
            self.assertTrue(pdf_file)
            self.assertTrue(pdf_file_called_after_activity)

    def test_activity2_download_as_pdf_async(self):
        activity_name = 'Demo - PDF exporting'
        activity = self.project.activity(name=activity_name)

        # testing
        with temp_chdir() as target_dir:
            activity.download_as_pdf(target_dir=target_dir, pdf_filename='pdf_file', include_appendices=True)
            pdf_file = os.path.join(target_dir, 'pdf_file.pdf')
            pdf_file_called_after_activity = os.path.join(target_dir, activity_name + '.pdf')
            self.assertTrue(pdf_file)
            self.assertTrue(pdf_file_called_after_activity)

    def test_activity2_assignees_list(self):
        activity_name = 'automated_created_task'
        activity = self.project.activity(name=activity_name)  # type: Activity2

        list_of_assignees_in_data = activity._json_data.get('assignees_ids')
        assignees_list = activity.assignees

        self.assertSetEqual(set(list_of_assignees_in_data), set([u.id for u in assignees_list]))

    def test_activity2_assignees_list_no_assignees_gives_empty_list(self):
        activity_name = 'Customized task'
        activity = self.project.activity(name=activity_name)  # type: Activity2

        list_of_assignees_in_data = activity._json_data.get('assignees_ids')
        assignees_list = activity.assignees

        self.assertListEqual(list(), activity.assignees, "Task has no assingees and should return Empty list")

import os
import warnings
from datetime import datetime
from unittest import skipIf

import pytest
import pytz
import requests

from pykechain.enums import ActivityType, ActivityStatus, ActivityClassification, Category, \
    activity_root_name_by_classification, ActivityRootNames
from pykechain.exceptions import NotFoundError, MultipleFoundError, IllegalArgumentError, APIError
from pykechain.models import Activity2
from pykechain.utils import temp_chdir
from tests.classes import TestBetamax
from tests.utils import TEST_FLAG_IS_WIM2

ISOFORMAT = "%Y-%m-%dT%H:%M:%SZ"
ISOFORMAT_HIGHPRECISION = "%Y-%m-%dT%H:%M:%S.%fZ"


class TestActivityConstruction(TestBetamax):

    def setUp(self):
        super().setUp()
        self.process = self.project.create_activity(
            name='__Test process',
            activity_type=ActivityType.PROCESS,
        )
        self.task = None

    def tearDown(self):
        for activity in [self.task, self.process]:
            if activity:
                try:
                    activity.delete()
                except APIError:
                    pass
        super().tearDown()

    def test_create_with_inputs(self):
        name = '__Testing task'
        description = 'My new task'
        status = ActivityStatus.OPEN
        now = datetime.now()
        activity_type = ActivityType.TASK
        classification = ActivityClassification.WORKFLOW

        # setUp
        self.task = self.client.create_activity(
            name=name,
            parent=self.process,
            status=status,
            description=description,
            start_date=now,
            due_date=now,
            activity_type=activity_type,
            classification=classification,
        )

        # testing
        self.assertIsInstance(self.task, Activity2)
        self.assertEqual(name, self.task.name)
        self.assertEqual(status, self.task.status)
        self.assertTrue(description, self.task.description)
        self.assertIsInstance(self.task.start_date, datetime)
        self.assertIsInstance(self.task.due_date, datetime)
        self.assertEqual(activity_type, self.task.activity_type)
        self.assertEqual(classification, self.task.classification)

    def test_create_on_scope(self):
        self.task = self.project.create_activity('__Test task')

        self.assertIsInstance(self.task, Activity2)
        self.assertEqual(ActivityType.TASK, self.task.activity_type)
        self.assertEqual(ActivityClassification.WORKFLOW, self.task.classification)

    def test_create_with_classification(self):

        for classification in ActivityClassification.values():
            with self.subTest(msg='Classification: {}'.format(classification)):
                # setUp 1
                root_name = activity_root_name_by_classification[classification]
                root = self.project.activity(name=root_name)

                # testing 1
                self.assertEqual(classification, root.classification)
                self.assertEqual(ActivityType.PROCESS, root.activity_type)

                # setUp 2
                task = self.client.create_activity(
                    parent=root,
                    name='{}'.format(classification),
                    classification=classification,
                )

                # testing 2
                self.assertEqual(classification, task.classification)

                # tearDown
                task.delete()

    def test_create_with_incorrect_classification(self):
        with self.assertRaises(IllegalArgumentError):
            self.project.create_activity(
                name='Impossible classification',
                classification='Gummy bears',
            )

    def test_create_with_incorrect_parent(self):
        with self.assertRaises(IllegalArgumentError):
            self.client.create_activity(
                name='Impossible parent',
                parent='Darth vader',
            )

    def test_create_with_task_as_parent(self):
        task = self.process.create(name='__Test task')

        with self.assertRaises(IllegalArgumentError, msg='Tasks cannot be created below other tasks!'):
            task.create('This cannot happen')

    def test_create_with_incorrect_inputs(self):
        with self.assertRaises(IllegalArgumentError):
            self.project.create_activity('__test_task', status='COMPLETE')

        with self.assertRaises(IllegalArgumentError):
            self.project.create_activity('__test_task', start_date=datetime.now().isoformat())

        with self.assertRaises(IllegalArgumentError):
            self.project.create_activity('__test_task', description=1234)

        with self.assertRaises(IllegalArgumentError):
            self.project.create_activity('__test_task', classification='PRODUCT')

    def test_delete(self):
        # setUp
        sub_process_name = '__Test subprocess'
        sub_task_name = '__Test subtask'

        subprocess = self.process.create(name=sub_process_name, activity_type=ActivityType.PROCESS)
        self.task = subprocess.create(name=sub_task_name)
        subprocess.delete()

        # testing
        with self.assertRaises(APIError, msg='Cant delete the same Activity twice!'):
            subprocess.delete()
        with self.assertRaises(NotFoundError, msg='Deleted Activity cant be found!'):
            self.project.activity(name=sub_process_name)
        with self.assertRaises(NotFoundError, msg='Children of deleted Activities cant be found!'):
            self.project.activity(name=sub_task_name)


class TestActivities(TestBetamax):
    def test_retrieve_activities(self):
        self.assertTrue(self.project.activities())

    def test_retrieve_single_activity(self):
        self.assertTrue(self.project.activity('Specify wheel diameter'))

    def test_activity_attributes(self):
        attributes = ['_client', '_json_data', 'id', 'name', 'created_at', 'updated_at', 'ref',
                      'description', 'status', 'activity_type', '_scope_id',
                      'start_date', 'due_date']

        obj = self.project.activity('Specify wheel diameter')
        for attribute in attributes:
            self.assertTrue(hasattr(obj, attribute),
                            "Could not find '{}' in the object: '{}'".format(attribute, obj.__dict__.keys()))

    def test_retrieve_unknown_activity(self):
        with self.assertRaises(NotFoundError):
            self.project.activity('Hello?!')

    def test_retrieve_too_many_activity(self):
        with self.assertRaises(MultipleFoundError):
            self.project.activity()

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

    def test_edit_cascade_down(self):
        # setup
        subprocess = self.project.activity('Subprocess')  # type: Activity2
        subtask = self.project.activity('SubTask')  # type: Activity2
        testuser = self.client.user(username='testuser')

        subprocess.edit_cascade_down(
            assignees=['testuser'],
            status=ActivityStatus.COMPLETED,
            overwrite=False,
        )

        subprocess.refresh()
        subtask.refresh()

        # testing
        self.assertIn(testuser, subprocess.assignees)
        self.assertIn(testuser, subtask.assignees)
        self.assertEqual(subprocess.status, ActivityStatus.COMPLETED)
        self.assertEqual(subtask.status, ActivityStatus.COMPLETED)

        # tearDown
        subprocess.edit(assignees=[], status=ActivityStatus.OPEN)
        subtask.edit(assignees=[], status=ActivityStatus.OPEN)

    def test_retrieve_children_of_task_fails_for_task(self):
        task = self.project.activity(name='Specify wheel diameter')
        with self.assertRaises(NotFoundError, msg='Tasks have no children!'):
            task.children()

    def test_child(self):
        workflow_root = self.project.activity(name=ActivityRootNames.WORKFLOW_ROOT)

        child_task = workflow_root.child(name='Specify wheel diameter')

        self.assertIsInstance(child_task, Activity2)
        self.assertEqual(child_task._json_data['parent_id'], workflow_root.id)

    def test_child_invalid(self):
        workflow_root = self.project.activity(name=ActivityRootNames.WORKFLOW_ROOT)

        with self.assertRaises(IllegalArgumentError):
            workflow_root.child()

        second_process = workflow_root.create(name='Specify wheel diameter')
        with self.assertRaises(MultipleFoundError):
            workflow_root.child(name='Specify wheel diameter')
        second_process.delete()

        with self.assertRaises(NotFoundError):
            workflow_root.child(name='Just a scratch')

    def test_retrieve_all_children(self):
        workflow_root = self.project.activity(name=ActivityRootNames.WORKFLOW_ROOT)

        all_tasks = workflow_root.all_children()

        self.assertIsInstance(all_tasks, list)
        self.assertEqual(12, len(all_tasks), msg='Number of tasks has changed, expected 12.')

    def test_retrieve_activity_by_id(self):
        task = self.project.activity(name='Subprocess')  # type: Activity2

        task_by_id = self.client.activity(pk=task.id)

        self.assertEqual(task.id, task_by_id.id)

    def test_retrieve_siblings_of_a_task_in_a_subprocess(self):
        task = self.project.activity(name='Subprocess')  # type: Activity2
        siblings = task.siblings()

        self.assertIn(task.id, [sibling.id for sibling in siblings])
        self.assertTrue(len(siblings) >= 1)

    # in 1.12

    def test_retrieve_siblings_of_a_task_in_a_subprocess_with_arguments(self):
        task = self.project.activity(name='SubTask')  # type: Activity2
        siblings = task.siblings(name__icontains='sub')

        self.assertIn(task.id, [sibling.id for sibling in siblings])
        self.assertEqual(1, len(siblings))

    @skipIf(not TEST_FLAG_IS_WIM2, reason="This tests is designed for WIM version 2, expected to fail on old WIM")
    def test_activity2_without_scope_id_will_fix_itself(self):
        specify_wheel_diam_cripled = self.project.activity(name='Specify wheel diameter', fields='id,name,status')
        self.assertFalse(specify_wheel_diam_cripled._json_data.get('scope_id'))

        # now the self-healing will begin
        self.assertEqual(specify_wheel_diam_cripled.scope_id, self.project.id)

    # in 1.13
    def test_create_activity_with_incorrect_activity_class_fails(self):
        with self.assertRaisesRegex(IllegalArgumentError, 'Please provide accepted activity_type'):
            self.project.create_activity(name='New', activity_type='DEFUNCTActivity')


@skipIf(not TEST_FLAG_IS_WIM2, reason="This tests is designed for WIM version 2, expected to fail on older WIM")
class TestActivity2SpecificTests(TestBetamax):
    # 2.0 new activity
    # noinspection PyTypeChecker
    def test_edit_activity2_assignee(self):
        specify_wd = self.project.activity('Specify wheel diameter')  # type: Activity2
        original_assignee_ids = specify_wd._json_data.get('assignee_ids') or []

        # pykechain_user = self.client.user(username='pykechain')
        test_user = self.client.user(username='testuser')

        specify_wd.edit(assignees_ids=[test_user.id])
        specify_wd.refresh()

        self.assertIsInstance(specify_wd._json_data.get('assignees_ids')[0], int)

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
        subprocess = self.project.activity(name='Subprocess')  # type: Activity2
        children = subprocess.children()
        self.assertTrue(len(children) >= 1)
        for child in children:
            self.assertEqual(child._json_data.get('parent_id'), subprocess.id)

    def test_activity2_retrieve_children_of_subprocess_with_arguments(self):
        subprocess = self.project.activity(name='Subprocess')  # type: Activity2
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
        # self.assertTrue(subprocess_subtask.subprocess())

    def test_activity2_is_task(self):
        specify_wd = self.project.activity('Specify wheel diameter')

        self.assertTrue(specify_wd.is_task())
        self.assertFalse(specify_wd.is_subprocess())

    def test_activity2_is_subprocess(self):
        subprocess = self.project.activity('Subprocess')

        self.assertTrue(subprocess.is_subprocess())
        self.assertFalse(subprocess.is_task())

    def test_activity2_assignees_list(self):
        activity_name = 'test task'
        activity = self.project.activity(name=activity_name)  # type: Activity2

        list_of_assignees_in_data = activity._json_data.get('assignees_ids')
        assignees_list = activity.assignees

        self.assertSetEqual(set(list_of_assignees_in_data), set([u.id for u in assignees_list]))

    def test_activity2_assignees_list_no_assignees_gives_empty_list(self):
        activity_name = 'Specify wheel diameter'
        activity = self.project.activity(name=activity_name)  # type: Activity2

        list_of_assignees_in_data = activity._json_data.get('assignees_ids')
        assignees_list = activity.assignees

        self.assertListEqual(list(), activity.assignees, "Task has no assingees and should return Empty list")

    def test_activity2_move(self):
        # setUp
        activity_name = 'test task'
        activity_to_be_moved = self.project.activity(name=activity_name)
        original_parent = activity_to_be_moved.parent()

        new_parent_name = 'Subprocess'
        new_parent = self.project.activity(name=new_parent_name)

        activity_to_be_moved.move(parent=new_parent)

        activity_to_be_moved.refresh()

        # testing
        self.assertTrue(activity_to_be_moved.parent().id == new_parent.id)

        # tearDown
        activity_to_be_moved.move(parent=original_parent.id)
        activity_to_be_moved.refresh()
        self.assertTrue(activity_to_be_moved.parent().id == original_parent.id)

    def test_activity2_move_under_task_parent(self):
        # setUp
        activity_name = 'test task'
        activity_to_be_moved = self.project.activity(name=activity_name)

        new_parent_name = 'Specify wheel diameter'
        new_parent = self.project.activity(name=new_parent_name)

        # testing
        with self.assertRaises(IllegalArgumentError):
            activity_to_be_moved.move(parent=new_parent)

    def test_activity2_move_under_part_object(self):
        # setUp
        activity_name = 'test task'
        activity_to_be_moved = self.project.activity(name=activity_name)

        new_parent_name = 'Bike'
        new_parent = self.project.part(name=new_parent_name)

        # testing
        with self.assertRaises(IllegalArgumentError):
            activity_to_be_moved.move(parent=new_parent)

    # tests added in 3.0
    def test_activity2_retrieve_with_refs(self):
        # setup
        test_task_ref = 'test-task'
        test_task_name = 'Test task'
        test_task_activity = self.project.activity(ref=test_task_ref)

        # testing
        self.assertIsInstance(test_task_activity, Activity2)
        self.assertTrue(test_task_activity.name, test_task_name)

    def test_activity2_associated_parts(self):
        # setUp
        activity_name = 'Task - Form + Tables + Service'
        activity = self.project.activity(name=activity_name)
        associated_models, associated_instances = activity.associated_parts()

        # testing
        for model in associated_models:
            self.assertTrue(model.category == Category.MODEL)
            if model.name == 'Bike':
                self.assertTrue(model.property(name='Gears').output)
                self.assertFalse(model.property(name='Total height').output)
                self.assertFalse(model.property(name='Picture').output)
                self.assertFalse(model.property(name='Description').output)
                self.assertTrue(model.property(name='Website').output)
                self.assertTrue(model.property(name='Sale?').output)

        for instance in associated_instances:
            self.assertTrue(instance.category == Category.INSTANCE)
        self.assertTrue(len(associated_models) == 3)
        self.assertTrue(len(associated_instances) == 4)

    def test_activity2_associated_objects_ids(self):
        # setUp
        activity_name = 'Task - Form + Tables + Service'
        activity = self.project.activity(name=activity_name)
        associated_object_ids = activity.associated_object_ids()

        # testing
        self.assertTrue(len(associated_object_ids) == 17)

    def test_activity2_parts_of_specific_type(self):
        # setUp
        activity_name = 'Task - Form + Tables + Service'
        bike_model = self.project.model(name="Bike")
        activity = self.project.activity(name=activity_name)
        associated_models = activity.parts(category=Category.MODEL)

        # testing
        for model in associated_models:
            self.assertTrue(model.category == Category.MODEL)
            if model.name == 'Bike':
                self.assertTrue(model.property(name='Gears').output)
                self.assertFalse(model.property(name='Total height').output)
                self.assertFalse(model.property(name='Picture').output)
                self.assertFalse(model.property(name='Description').output)
                self.assertTrue(model.property(name='Website').output)
                self.assertTrue(model.property(name='Sale?').output)
        self.assertTrue(len(associated_models) == 3)


# @skip('Does not work in PIM2 until KEC-19193 is resolved')
class TestActivityDownloadAsPDF(TestBetamax):

    def test_activity2_download_as_pdf(self):
        # setUp
        activity_name = 'Task - Form'
        activity = self.project.activity(name=activity_name)

        # testing
        with temp_chdir() as target_dir:
            activity.download_as_pdf(target_dir=target_dir, pdf_filename='pdf_file')
            activity.download_as_pdf(target_dir=target_dir)
            pdf_file = os.path.join(target_dir, 'pdf_file.pdf')
            pdf_file_called_after_activity = os.path.join(target_dir, activity_name + '.pdf')
            self.assertTrue(pdf_file)
            self.assertTrue(pdf_file_called_after_activity)

    @pytest.mark.skipif("os.getenv('TRAVIS', False) or os.getenv('GITHUB_ACTIONS', False)",
                        reason="Skipping tests when using Travis or Github Actions, as not Auth can be provided")
    def test_activity2_download_as_pdf_async(self):
        activity_name = 'Task - Form + Tables + Service'
        activity = self.project.activity(name=activity_name)

        # testing
        with temp_chdir() as target_dir:
            activity.download_as_pdf(target_dir=target_dir, pdf_filename='pdf_file', include_appendices=True)
            pdf_file = os.path.join(target_dir, 'pdf_file.pdf')
            pdf_file_called_after_activity = os.path.join(target_dir, activity_name + '.pdf')
            self.assertTrue(pdf_file)
            self.assertTrue(pdf_file_called_after_activity)

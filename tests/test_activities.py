import os
import warnings
from datetime import datetime

import pytest
import pytz
import requests

from pykechain.enums import (
    ActivityClassification,
    ActivityRootNames,
    ActivityStatus,
    ActivityType,
    Category,
    Classification,
    Multiplicity,
    NotificationEvent,
    PaperOrientation,
    PaperSize,
    PropertyType,
    activity_root_name_by_classification,
)
from pykechain.exceptions import (
    APIError,
    IllegalArgumentError,
    MultipleFoundError,
    NotFoundError,
)
from pykechain.models import Activity
from pykechain.models.representations import CustomIconRepresentation
from pykechain.utils import slugify_ref, temp_chdir
from tests.classes import TestBetamax

ISOFORMAT = "%Y-%m-%dT%H:%M:%SZ"
ISOFORMAT_HIGHPRECISION = "%Y-%m-%dT%H:%M:%S.%fZ"


class TestActivityConstruction(TestBetamax):
    def setUp(self):
        super().setUp()
        self.process = self.project.create_activity(
            name="__Test process",
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
        name = "Testing task"
        ref = slugify_ref(name)
        description = "My new task"
        status = ActivityStatus.OPEN
        activity_type = ActivityType.TASK
        classification = ActivityClassification.WORKFLOW

        # setUp
        self.task = self.client.create_activity(
            name=name,
            ref=ref,
            parent=self.process,
            status=status,
            description=description,
            start_date=self.time,
            due_date=self.time,
            activity_type=activity_type,
            classification=classification,
            activity_options=dict(
                representations=[
                    CustomIconRepresentation(value="pennant").as_json(),
                ],
            ),
        )

        # testing
        self.assertIsInstance(self.task, Activity)
        self.assertEqual(name, self.task.name)
        self.assertEqual(ref, self.task.ref)
        self.assertEqual(status, self.task.status)
        self.assertTrue(description, self.task.description)
        self.assertIsInstance(self.task.start_date, datetime)
        self.assertIsInstance(self.task.due_date, datetime)
        self.assertEqual(activity_type, self.task.activity_type)
        self.assertEqual(classification, self.task.classification)

    def test_create_on_scope(self):
        self.task = self.project.create_activity("__Test task")

        self.assertIsInstance(self.task, Activity)
        self.assertEqual(ActivityType.TASK, self.task.activity_type)
        self.assertEqual(ActivityClassification.WORKFLOW, self.task.classification)

    def test_create_below_parent(self):
        self.process.children()  # populate `_cached_children`.
        self.assertIsNotNone(
            self.process._cached_children, "Cached children should be an (empty) list."
        )

        new_task = self.process.create(
            name="__Testing task",
            activity_type=ActivityType.TASK,
        )

        current_children = self.process.children()

        self.assertTrue(current_children)
        self.assertIn(
            new_task,
            current_children,
            msg="New child task should be among the children.",
        )

    def test_create_with_classification(self):
        for classification in ActivityClassification.values():
            with self.subTest(msg=f"Classification: {classification}"):
                # setUp 1
                root_name = activity_root_name_by_classification[classification]
                root = self.project.activity(name=root_name)

                # testing 1
                self.assertEqual(classification, root.classification)
                self.assertEqual(ActivityType.PROCESS, root.activity_type)

                # setUp 2
                task = self.client.create_activity(
                    parent=root,
                    name=f"{classification}",
                    classification=classification,
                )

                # testing 2
                self.assertEqual(classification, task.classification)

                # tearDown
                task.delete()

    def test_create_with_incorrect_classification(self):
        with self.assertRaises(IllegalArgumentError):
            self.project.create_activity(
                name="Impossible classification",
                classification="Gummy bears",
            )

    def test_create_with_incorrect_parent(self):
        with self.assertRaises(IllegalArgumentError):
            self.client.create_activity(
                name="Impossible parent",
                parent="Darth vader",
            )

    def test_create_with_task_as_parent(self):
        task = self.process.create(name="__Test task")

        with self.assertRaises(
            IllegalArgumentError, msg="Tasks cannot be created below other tasks!"
        ):
            task.create("This cannot happen")

    def test_create_with_incorrect_inputs(self):
        with self.assertRaises(IllegalArgumentError):
            self.project.create_activity("__test_task", status="COMPLETE")

        with self.assertRaises(IllegalArgumentError):
            self.project.create_activity("__test_task", start_date=4)

        with self.assertRaises(IllegalArgumentError):
            self.project.create_activity("__test_task", description=1234)

        with self.assertRaises(IllegalArgumentError):
            self.project.create_activity("__test_task", classification="PRODUCT")

    def test_delete(self):
        # setUp
        sub_process_name = "__Test subprocess"
        sub_task_name = "__Test subtask"

        subprocess = self.process.create(
            name=sub_process_name, activity_type=ActivityType.PROCESS
        )
        self.task = subprocess.create(name=sub_task_name)
        subprocess.delete()

        # testing
        with self.assertRaises(APIError, msg="Cant delete the same Activity twice!"):
            subprocess.delete()
        with self.assertRaises(NotFoundError, msg="Deleted Activity cant be found!"):
            self.project.activity(name=sub_process_name)
        with self.assertRaises(
            NotFoundError, msg="Children of deleted Activities cant be found!"
        ):
            self.project.activity(name=sub_task_name)


class TestActivityClone(TestBetamax):
    def setUp(self):
        super().setUp()
        self.process = self.project.create_activity(
            name="__TEST CLONE SUBPROCESS", activity_type=ActivityType.PROCESS
        )
        self.task = self.process.create("__TEST CLONE TASK")
        self.clone = None
        self.bucket = [self.process]

    def tearDown(self):
        for activity in self.bucket:
            if activity:
                try:
                    activity.delete()
                except APIError:
                    pass
        super().tearDown()

    def test(self):
        clone = self.task.clone()

        self.assertIsInstance(clone, Activity)
        self.assertNotEqual(self.task, clone)
        self.assertEqual(self.task.parent_id, clone.parent_id)

    def test_parent_id(self):
        second_process = self.project.create_activity(
            name="__Test process 2",
            activity_type=ActivityType.PROCESS,
        )
        self.bucket.append(second_process)

        clone = self.task.clone(
            parent=second_process,
        )

        self.assertNotEqual(self.task.parent_id, clone.parent_id)

    def test_update(self):
        new_name = "__TEST TASK RENAMED"
        clone = self.task.clone(
            update_dict=dict(name=new_name),
        )

        self.assertEqual(new_name, clone.name)

    def test_update_incorrect(self):
        with self.assertRaises(IllegalArgumentError):
            self.task.clone(part_parent_instance=True)

    def test_async_via_task(self):
        response = self.task.clone(asynchronous=True)

        self.assertIsNone(response)

    def test_async_via_client(self):
        response = self.client.clone_activities(
            activities=[self.task], activity_parent=self.process, asynchronous=True
        )

        self.assertIsInstance(response, list)
        self.assertFalse(response)


class TestActivityCloneParts(TestBetamax):
    def setUp(self):
        super().setUp()

        # Create task to clone
        self.process = self.project.create_activity(
            name="__TEST CLONE SUBPROCESS", activity_type=ActivityType.PROCESS
        )
        self.task = self.process.create(name="__TEST CLONE TASK")

        # Create part model to copy along
        intermediate = self.project.catalog_root_model.add_model(
            name="__TEST CLONE INTERMEDIATE MODEL", multiplicity=Multiplicity.ONE
        )
        source_parent_model = intermediate.add_model(
            name="__TEST CLONE CONFIGURED MODEL - PARENT",
            multiplicity=Multiplicity.ONE_MANY,
        )
        child_model = source_parent_model.add_model(
            name="__TEST CLONE CONFIGURED MODEL - CHILD",
            multiplicity=Multiplicity.ONE_MANY,
        )

        for prop_type in [
            PropertyType.CHAR_VALUE,
            PropertyType.DATE_VALUE,
        ]:
            child_model.add_property(
                name="__TEST " + prop_type, property_type=prop_type
            )

        # Add widget to add configured part models
        wm = self.task.widgets()
        wm.add_filteredgrid_widget(
            parent_instance=source_parent_model.instance(),
            part_model=child_model,
            all_readable=True,
        )

        self.bike_model = self.project.model("Bike")
        self.bike_instance = self.bike_model.instance()
        wm.add_propertygrid_widget(
            part_instance=self.bike_instance,
            all_readable=True,
        )

        # Create target parents to move to
        self.target_parent_model = self.project.product_root_model.add_model(
            name="__TEST CLONE TARGET PARENT", multiplicity=Multiplicity.ONE
        )
        self.parent_instance = self.target_parent_model.instance()

        # In tearDown, delete tasks first, then configured data models
        self.bucket = [self.task, self.process, intermediate, self.target_parent_model]

    def tearDown(self):
        for obj in self.bucket:
            if obj:
                try:
                    obj.delete()
                except APIError:
                    pass
        super().tearDown()

    def test(self):
        """Copy a data model from the catalog to the product data model tree"""
        clones = self.client.clone_activities(
            activities=[self.task],
            activity_parent=self.process,
            activity_update_dicts={
                self.task.id: {"name": "__TEST CLONE ACTIVITY WITH PARTS"}
            },
            include_part_models=True,
            include_part_instances=True,
            include_children=True,
            part_parent_model=self.target_parent_model,
            part_parent_instance=self.parent_instance,
            asynchronous=False,
        )

        self.assertTrue(clones)

        new_children = list(self.parent_instance.children())
        self.assertTrue(new_children, msg="No parts were copied")

    def test_excluded_models(self):
        """Exclude the bike model from the copy"""
        clones = self.client.clone_activities(
            activities=[self.task],
            activity_parent=self.process,
            activity_update_dicts={
                self.task.id: {"name": "__TEST CLONE ACTIVITY WITH PARTS"}
            },
            include_part_models=True,
            include_part_instances=True,
            include_children=True,
            excluded_parts=[self.bike_model, self.bike_instance],
            part_parent_model=self.target_parent_model,
            part_parent_instance=self.parent_instance,
            asynchronous=False,
        )

        self.assertTrue(clones)

        new_children = list(self.parent_instance.children())
        self.assertTrue(new_children, msg="No parts were copied")
        self.assertNotIn(
            "Bike",
            {c.name for c in new_children},
            msg=(
                "Bike should not have been copied over. "
                "Actually it is not copied over, it is moved to the parent_instance"
            ),
        )


class TestActivities(TestBetamax):
    NAME = "TEST ACTIVITY"

    def setUp(self):
        super().setUp()
        self.workflow_root = self.project.activity(name=ActivityRootNames.WORKFLOW_ROOT)
        self.task = self.project.create_activity(
            name=self.NAME, activity_type=ActivityType.TASK
        )

    def tearDown(self):
        if self.task:
            try:
                self.task.delete()
            except APIError:
                pass
        super().tearDown()

    def test_retrieve_activities(self):
        self.assertTrue(self.project.activities())

    def test_retrieve_single_activity(self):
        self.assertTrue(self.project.activity(self.NAME))

    def test_activity_attributes(self):
        attributes = [
            "_client",
            "_json_data",
            "id",
            "name",
            "created_at",
            "updated_at",
            "ref",
            "description",
            "status",
            "activity_type",
            "_scope_id",
            "start_date",
            "due_date",
            "_form_collection",
        ]

        for attribute in attributes:
            with self.subTest(msg=attribute):
                self.assertTrue(
                    hasattr(self.task, attribute),
                    "Could not find '{}' in the object: '{}'".format(
                        attribute, self.task.__dict__.keys()
                    ),
                )

    def test_retrieve_unknown_activity(self):
        with self.assertRaises(NotFoundError):
            self.project.activity("Hello?!")

    def test_retrieve_too_many_activity(self):
        with self.assertRaises(MultipleFoundError):
            self.project.activity()

    # new in 1.7
    def test_edit_activity_name(self):
        self.task.edit(name="Specify wheel diameter - updated")

        self.task_u = self.project.activity("Specify wheel diameter - updated")
        self.assertEqual(self.task.id, self.task_u.id)
        self.assertEqual(self.task.name, self.task_u.name)
        self.assertEqual(self.task.name, "Specify wheel diameter - updated")

        # Added to improve coverage. Assert whether IllegalArgumentError is raised when 'name' is not a string object.
        with self.assertRaises(IllegalArgumentError):
            self.task.edit(name=True)

    def test_edit_activity_description(self):
        self.task.edit(description="This task has a cool description")

        self.assertEqual(self.task._client.last_response.status_code, requests.codes.ok)

        # Added to improve coverage. Assert whether IllegalArgumentError is raised when 'description' is
        # not a string object.
        with self.assertRaises(IllegalArgumentError):
            self.task.edit(description=42)

    def test_edit_activity_naive_dates(self):
        start_time = datetime(2000, 1, 1, 0, 0, 0)
        due_time = datetime(2019, 12, 31, 0, 0, 0)

        with warnings.catch_warnings(record=False):
            warnings.simplefilter("ignore")
            self.task.edit(start_date=start_time, due_date=due_time)

        self.assertEqual(self.task._client.last_response.status_code, requests.codes.ok)

        with self.assertRaises(IllegalArgumentError):
            self.task.edit(start_date="All you need is love")

        with self.assertRaises(IllegalArgumentError):
            self.task.edit(due_date="Love is all you need")

    def test_edit_due_date_timezone_aware(self):
        self.task.edit(start_date=self.time, due_date=self.time)

        self.assertEqual(self.task._client.last_response.status_code, requests.codes.ok)

    # 1.10.0
    def test_edit_activity_status(self):
        self.task.edit(status=ActivityStatus.COMPLETED)

        for status in [True, "NO STATUS", 3]:
            with self.subTest(msg=status):
                with self.assertRaises(IllegalArgumentError):
                    self.task.edit(status=status)

    # 1.7.2
    def test_datetime_with_naive_duedate_only_fails(self):
        """reference to #121 - thanks to @joost.schut"""
        naive_duedate = datetime(2017, 6, 5, 5, 0, 0)

        with warnings.catch_warnings(record=False):
            warnings.simplefilter("ignore")
            self.task.edit(due_date=naive_duedate)

    def test_datetime_with_tzinfo_provides_correct_offset(self):
        """reference to #121 - thanks to @joost.schut

        The tzinfo.timezone('Europe/Amsterdam') should provide a 2 hour offset, recording 20 minutes
        """
        # setup
        tz = pytz.timezone("Europe/Amsterdam")
        tzaware_due = tz.localize(datetime(2017, 7, 1))
        tzaware_start = tz.localize(datetime(2017, 6, 30, 0, 0, 0))

        self.task.edit(start_date=tzaware_start)
        self.assertTrue(
            self.task._json_data["start_date"], tzaware_start.isoformat(sep="T")
        )

        self.task.edit(due_date=tzaware_due)
        self.assertTrue(
            self.task._json_data["due_date"], tzaware_due.isoformat(sep="T")
        )

    def test_edit_cascade_down(self):
        # setup
        subprocess = self.project.activity("Subprocess")  # type: Activity
        subtask = self.project.activity("SubTask")  # type: Activity
        testuser = self.client.user(username="testuser")

        subprocess.edit_cascade_down(
            assignees=["testuser"],
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

    # test added due to #847 - providing no inputs overwrites values
    def test_edit_activity_clearing_values(self):
        # setup
        initial_name = "Pykechain testing task"
        initial_description = "Task created to test editing."
        initial_start_date = datetime(2018, 12, 5, tzinfo=None)
        initial_due_date = datetime(2018, 12, 8, tzinfo=None)
        initial_tags = ["tag_one", "tag_two"]
        initial_assignee = self.client.user(username="testuser")

        self.task.edit(
            name=initial_name,
            description=initial_description,
            tags=initial_tags,
            start_date=initial_start_date,
            due_date=initial_due_date,
            assignees=[initial_assignee.username],
        )

        # Edit without mentioning values, everything should stay the same
        new_name = "New name for task"
        self.task.edit(name=new_name)

        # testing
        self.assertEqual(self.task.name, new_name)
        self.assertEqual(self.task.description, initial_description)
        self.assertEqual(
            self.task.start_date.strftime("%Y/%m/%d, %H:%M:%S"),
            initial_start_date.strftime("%Y/%m/%d, %H:%M:%S"),
        )
        self.assertEqual(
            self.task.due_date.strftime("%Y/%m/%d, %H:%M:%S"),
            initial_due_date.strftime("%Y/%m/%d, %H:%M:%S"),
        )
        self.assertEqual(self.task.tags, initial_tags)

        # Edit with clearing the values, name and status cannot be cleared
        self.task.edit(
            name=None,
            description=None,
            tags=None,
            start_date=None,
            due_date=None,
            status=None,
            assignees=None,
        )
        self.task.refresh()
        self.assertEqual(self.task.name, new_name)
        self.assertEqual(self.task.description, "")
        self.assertEqual(self.task.start_date, None)
        self.assertEqual(self.task.due_date, None)
        self.assertEqual(self.task.assignees, list())
        self.assertEqual(self.task.tags, list())

    def test_retrieve_children_of_task_fails_for_task(self):
        with self.assertRaises(NotFoundError, msg="Tasks have no children!"):
            self.task.children()

    def test_child(self):
        child_task = self.workflow_root.child(name=self.NAME)

        self.assertIsInstance(child_task, Activity)
        self.assertEqual(child_task._json_data["parent_id"], self.workflow_root.id)

    def test_child_invalid(self):
        with self.assertRaises(IllegalArgumentError):
            self.workflow_root.child()

        second_process = self.workflow_root.create(name=self.NAME)
        with self.assertRaises(MultipleFoundError):
            self.workflow_root.child(name=self.NAME)
        second_process.delete()

        with self.assertRaises(NotFoundError):
            self.workflow_root.child(name="Just a scratch")

    def test_retrieve_all_children(self):
        all_tasks = self.workflow_root.all_children()

        self.assertIsInstance(all_tasks, list)
        self.assertEqual(
            13, len(all_tasks), msg="Number of tasks has changed, expected 12."
        )

    def test_retrieve_activity_by_id(self):
        task = self.project.activity(name="Subprocess")  # type: Activity

        task_by_id = self.client.activity(pk=task.id)

        self.assertEqual(task.id, task_by_id.id)

    def test_retrieve_siblings_of_a_task_in_a_subprocess(self):
        task = self.project.activity(name="Subprocess")  # type: Activity
        siblings = task.siblings()

        self.assertIn(task.id, [sibling.id for sibling in siblings])
        self.assertTrue(len(siblings) >= 1)

    def test_retrieve_siblings_of_root(self):
        with self.assertRaises(NotFoundError):
            self.workflow_root.siblings()

    # in 1.12

    def test_retrieve_siblings_of_a_task_in_a_subprocess_with_arguments(self):
        task = self.project.activity(name="SubTask")  # type: Activity
        siblings = task.siblings(name__icontains="sub")

        self.assertIn(task.id, [sibling.id for sibling in siblings])
        self.assertEqual(1, len(siblings))

    def test_activity_without_scope_id_will_fix_itself(self):
        specify_wheel_diam_cripled = self.project.activity(
            name="Specify wheel diameter", fields="id,name,status"
        )
        self.assertFalse(specify_wheel_diam_cripled._json_data.get("scope_id"))

        # now the self-healing will begin
        self.assertEqual(specify_wheel_diam_cripled.scope_id, self.project.id)

    # in 1.13
    def test_create_activity_with_incorrect_activity_class_fails(self):
        with self.assertRaisesRegex(
            IllegalArgumentError, "must be an option from enum"
        ):
            self.project.create_activity(name="New", activity_type="DEFUNCTActivity")

    # 2.0 new activity
    # noinspection PyTypeChecker
    def test_edit_activity_assignee(self):
        specify_wd = self.project.activity("Specify wheel diameter")  # type: Activity
        original_assignee_ids = specify_wd._json_data.get("assignee_ids") or []

        # pykechain_user = self.client.user(username='pykechain')
        test_user = self.client.user(username="testuser")

        specify_wd.edit(assignees_ids=[test_user.id])
        specify_wd.refresh()

        self.assertIsInstance(specify_wd._json_data.get("assignees_ids")[0], int)

        self.assertEqual(
            specify_wd._client.last_response.status_code, requests.codes.ok
        )

        # Added to improve coverage. Assert whether NotFoundError is raised when 'assignee' is not part of the
        # scope members
        with self.assertRaises(NotFoundError):
            specify_wd.edit(assignees_ids=[-100])

        # Added to improve coverage. Assert whether NotFoundError is raised when 'assignee' is not part of the
        # scope members
        with self.assertRaises(IllegalArgumentError):
            specify_wd.edit(assignees_ids="this should have been a list")

        specify_wd.edit(assignees_ids=original_assignee_ids)

    def test_activity_retrieve_parent_of_task(self):
        task = self.project.activity(name="SubTask")
        subprocess = task.parent()  # type Activity
        self.assertEqual(subprocess.activity_type, ActivityType.PROCESS)

    def test_activity_retrieve_parent_of_root(self):
        task = self.project.activity(name=ActivityRootNames.WORKFLOW_ROOT)
        with self.assertRaises(NotFoundError):
            task.parent()

    def test_activity_retrieve_parent_of_a_toplevel_task_returns_workflow_root_id(
        self,
    ):
        task = self.project.activity("Specify wheel diameter")
        parent = task.parent()
        self.assertEqual(self.project._json_data.get("workflow_root_id"), parent.id)

    def test_activity_test_workflow_root_object(self):
        workflow_root = self.project.activity(
            id=self.project._json_data.get("workflow_root_id")
        )

        self.assertTrue(workflow_root.is_root())
        self.assertTrue(workflow_root.is_workflow_root())

    def test_activity_retrieve_children_of_parent(self):
        subprocess = self.project.activity(name="Subprocess")  # type: Activity
        children = subprocess.children()
        self.assertTrue(len(children) >= 1)
        for child in children:
            self.assertEqual(child._json_data.get("parent_id"), subprocess.id)

    def test_activity_retrieve_children_of_subprocess_with_arguments(self):
        subprocess = self.project.activity(name="Subprocess")  # type: Activity
        children = subprocess.children(name__icontains="task")
        self.assertTrue(len(children) >= 1)
        for child in children:
            self.assertEqual(child._json_data.get("parent_id"), subprocess.id)

    def test_count_children(self):
        process = self.project.activity(name="Tasks with Widgets")
        nr = process.count_children()

        self.assertIsInstance(nr, int)
        self.assertEqual(8, nr)

        nr = process.count_children(name__contains="Service")
        self.assertEqual(4, nr)

        with self.assertRaises(IllegalArgumentError):
            self.task.count_children()

    def test_rootlevel_activity_is_rootlevel(self):
        specify_wd = self.project.activity("Specify wheel diameter")

        self.assertTrue(specify_wd.is_rootlevel())

        root_itself = self.project.activity(ActivityRootNames.WORKFLOW_ROOT)

        self.assertFalse(root_itself.is_rootlevel())

    def test_subtask_activity_is_not_rootlevel(self):
        subprocess_subtask = self.project.activity("SubTask")

        self.assertFalse(subprocess_subtask.is_rootlevel())

    def test_activity_is_task(self):
        specify_wd = self.project.activity("Specify wheel diameter")

        self.assertTrue(specify_wd.is_task())
        self.assertFalse(specify_wd.is_subprocess())

    def test_activity_is_subprocess(self):
        subprocess = self.project.activity("Subprocess")

        self.assertTrue(subprocess.is_subprocess())
        self.assertFalse(subprocess.is_task())

    def test_activity_assignees_list(self):
        test_user = self.client.user(username="testuser")
        self.task.edit(assignees_ids=[test_user.id])
        self.task.refresh()

        list_of_assignees_in_data = self.task._json_data.get("assignees_ids")
        assignees_list = self.task.assignees

        self.assertSetEqual(
            set(list_of_assignees_in_data), {u.id for u in assignees_list}
        )

    def test_activity_assignees_list_no_assignees_gives_empty_list(self):
        activity_name = "Specify wheel diameter"
        activity = self.project.activity(name=activity_name)  # type: Activity

        self.assertListEqual(
            list(),
            activity.assignees,
            "Task has no assignees and should return Empty list",
        )

    def test_activity_move(self):
        # setUp
        activity_to_be_moved = self.task

        new_parent_name = "Subprocess"
        new_parent = self.project.activity(name=new_parent_name)

        activity_to_be_moved.move(parent=new_parent)

        # testing
        self.assertEqual(new_parent, activity_to_be_moved.parent())

    def test_activity_move_under_task_parent(self):
        # setUp
        new_parent_name = "Specify wheel diameter"
        new_parent = self.project.activity(name=new_parent_name)

        # testing
        with self.assertRaises(IllegalArgumentError):
            self.task.move(parent=new_parent)

    def test_activity_move_under_part_object(self):
        # setUp
        new_parent_name = "Bike"
        new_parent = self.project.part(name=new_parent_name)

        # testing
        with self.assertRaises(IllegalArgumentError):
            self.task.move(parent=new_parent)

    # tests added in 3.0
    def test_activity_retrieve_with_refs(self):
        # setup
        test_task_ref = slugify_ref(self.task.name)
        test_task_activity = self.project.activity(ref=test_task_ref)

        # testing
        self.assertIsInstance(test_task_activity, Activity)
        self.assertEqual(self.task, test_task_activity)

    def test_activity_associated_parts(self):
        # setUp
        activity_name = "Task - Form + Tables + Service"
        activity = self.project.activity(name=activity_name)
        associated_models, associated_instances = activity.associated_parts()

        # testing
        for model in associated_models:
            self.assertTrue(model.category == Category.MODEL)
            if model.name == "Bike":
                self.assertTrue(model.property(name="Gears").output)
                self.assertFalse(model.property(name="Total height").output)
                self.assertFalse(model.property(name="Picture").output)
                self.assertFalse(model.property(name="Description").output)
                self.assertTrue(model.property(name="Website").output)
                self.assertTrue(model.property(name="Sale?").output)

        for instance in associated_instances:
            self.assertTrue(instance.category == Category.INSTANCE)
        self.assertTrue(len(associated_models) == 3)
        self.assertTrue(len(associated_instances) == 4)

    def test_activity_associated_objects_ids(self):
        # setUp
        activity_name = "Task - Form + Tables + Service"
        activity = self.project.activity(name=activity_name)
        associated_object_ids = activity.associated_object_ids()

        # testing
        self.assertTrue(len(associated_object_ids) == 17)

    def test_activity_parts_of_specific_type(self):
        # setUp
        activity_name = "Task - Form + Tables + Service"
        bike_model = self.project.model(name="Bike")
        activity = self.project.activity(name=activity_name)
        associated_models = activity.parts(category=Category.MODEL)

        # testing
        for model in associated_models:
            self.assertTrue(model.category == Category.MODEL)
            if model == bike_model:
                self.assertTrue(model.property(name="Gears").output)
                self.assertFalse(model.property(name="Total height").output)
                self.assertFalse(model.property(name="Picture").output)
                self.assertFalse(model.property(name="Description").output)
                self.assertTrue(model.property(name="Website").output)
                self.assertTrue(model.property(name="Sale?").output)
        self.assertTrue(len(associated_models) == 3)

    def test_activity_retrieve_form_collection(self):
        forms = self.project.forms(classification=Classification.CATALOG)
        for status_form in forms[0].status_forms:
            self.assertEqual(status_form.activity._form_collection, forms[0].id)


@pytest.mark.skipif(
    "os.getenv('TRAVIS', False) or os.getenv('GITHUB_ACTIONS', False)",
    reason="Skipping tests when using Travis or Github Actions, as downloads cannot be provided",
)
class TestActivityDownloadAsPDF(TestBetamax):
    def setUp(self):
        super().setUp()
        self.activity_name = "Task - Form"
        self.activity = self.project.activity(name=self.activity_name)
        self.user = self.client.user(id=3)  # testmanager

    def test_activity_download_as_pdf(self):
        # testing
        with temp_chdir() as target_dir:
            pdf_file = self.activity.download_as_pdf(
                target_dir=target_dir, pdf_filename="pdf_file", user=self.user
            )
            self.assertTrue(os.path.exists(pdf_file))
            self.assertTrue(pdf_file.endswith(".pdf"))
            pdf_file_called_after_activity = self.activity.download_as_pdf(
                target_dir=target_dir,
            )
            self.assertTrue(os.path.exists(pdf_file_called_after_activity))
            self.assertTrue(pdf_file_called_after_activity.endswith(".pdf"))

    def test_activity_download_as_pdf_async(self):
        # testing
        with temp_chdir() as target_dir:
            pdf_file = self.activity.download_as_pdf(
                target_dir=target_dir,
                pdf_filename="pdf_file",
                include_appendices=True,
                include_qr_code=True,
            )
            self.assertTrue(os.path.exists(pdf_file))
            self.assertTrue(pdf_file.endswith(".pdf"))

    def test_activity_download_as_pdf_without_inline_pdfs(self):
        # testing
        with temp_chdir() as target_dir:
            zip_file = self.activity.download_as_pdf(
                target_dir=target_dir,
                pdf_filename="pdf_file",
                user=self.user,
                as_zip=True,
            )
            self.assertTrue(os.path.exists(zip_file))
            self.assertTrue(zip_file.endswith(".zip"))

    def test_activity_share_link(self):
        # setUp
        test_user = self.client.user(username="testuser")

        message = "EXAMPLE_MESSAGE"
        subject = "EXAMPLE_SUBJECT"
        recipient_users = [test_user]

        self.activity.share_link(
            subject=subject,
            message=message,
            recipient_users=recipient_users,
        )

        # testing
        notifications = self.client.notifications(
            subject=subject,
            message=message,
            event=NotificationEvent.SHARE_ACTIVITY_LINK,
        )
        self.assertEqual(self.client.last_response.status_code, requests.codes.ok)
        self.assertTrue(len(notifications), 1)

        # tearDown
        notifications[0].delete()

    def test_activity_share_pdf(self):
        # setUp
        test_user = self.client.user(username="testuser")
        message = "EXAMPLE_MESSAGE"
        subject = "EXAMPLE_SUBJECT"
        paper_size = PaperSize.A2
        paper_orientation = PaperOrientation.PORTRAIT
        recipient_users = [test_user]

        self.activity.share_pdf(
            subject=subject,
            message=message,
            recipient_users=recipient_users,
            paper_size=paper_size,
            paper_orientation=paper_orientation,
            include_appendices=False,
            include_qr_code=True,
        )

        # testing
        notifications = self.client.notifications(
            subject=subject, message=message, event=NotificationEvent.SHARE_ACTIVITY_PDF
        )
        self.assertEqual(self.client.last_response.status_code, requests.codes.ok)
        self.assertTrue(len(notifications), 1)

        # tearDown
        notifications[0].delete()

    def test_activity_share_pdf_with_from_user(self):
        # setUp
        test_user = self.client.user(username="anotheruser")
        from_user = self.client.user(username="testuser")
        message = "EXAMPLE_MESSAGE"
        subject = "EXAMPLE_SUBJECT"
        paper_size = PaperSize.A2
        paper_orientation = PaperOrientation.PORTRAIT
        recipient_users = [test_user]

        self.activity.share_pdf(
            from_user=from_user,
            subject=subject,
            message=message,
            recipient_users=recipient_users,
            paper_size=paper_size,
            paper_orientation=paper_orientation,
            include_appendices=False,
            include_qr_code=True,
        )

        # testing
        notifications = self.client.notifications(
            subject=subject, message=message, event=NotificationEvent.SHARE_ACTIVITY_PDF
        )
        self.assertEqual(self.client.last_response.status_code, requests.codes.ok)
        self.assertTrue(len(notifications), 1)

        # tearDown
        notifications[0].delete()

    def test_activity_share_link_with_from_user(self):
        # setUp
        test_user = self.client.user(username="anotheruser")
        from_user = self.client.user(username="testuser")

        message = "EXAMPLE_MESSAGE"
        subject = "EXAMPLE_SUBJECT"
        recipient_users = [test_user]

        self.activity.share_link(
            from_user=from_user,
            subject=subject,
            message=message,
            recipient_users=recipient_users,
        )

        # testing
        notifications = self.client.notifications(
            subject=subject,
            message=message,
            event=NotificationEvent.SHARE_ACTIVITY_LINK,
        )
        self.assertEqual(self.client.last_response.status_code, requests.codes.ok)
        self.assertTrue(len(notifications), 1)

        # tearDown
        notifications[0].delete()


class TestActivityCloneWidgets(TestBetamax):
    def setUp(self):
        super().setUp()

        self.form = self.project.form(name="Test Cloning Widgets")
        self.workflow = self.project.workflow(name="Simple Form Flow")
        self.activity_status_to_do = self.form.status_forms[0].activity
        self.activity_status_in_progress = self.form.status_forms[1].activity
        self.new_activity = None
        self.new_form_template = None

    def tearDown(self):
        wm = self.activity_status_in_progress.widgets()
        wm.delete_all_widgets()

        if self.new_form_template:
            self.new_form_template.delete()
        if self.new_activity:
            self.new_activity.delete()
        super().tearDown()

    def test_clone_widgets(self):
        self.activity_status_in_progress.clone_widgets(
            from_activity=self.activity_status_to_do
        )

        wm_to_do = self.activity_status_to_do.widgets()
        wm_in_progress = self.activity_status_in_progress.widgets()

        for widget in wm_in_progress:
            self.assertIn(widget.title, [w.title for w in wm_to_do])

    def test_clone_widgets_cross_form(self):
        self.new_form_template = self.project.create_form_model(
            name="Test cross form widget cloning", workflow=self.workflow, contexts=[]
        )
        self.new_form_template_status_to_do = self.new_form_template.status_forms[
            0
        ].activity

        with self.assertRaises(APIError):
            self.new_form_template_status_to_do.clone_widgets(
                from_activity=self.activity_status_to_do
            )

    def test_clone_widget_to_an_activity(self):
        self.new_activity = self.project.create_activity(
            name="Test cross activity widget cloning", activity_type=ActivityType.TASK
        )

        with self.assertRaises(APIError):
            self.new_activity.clone_widgets(from_activity=self.activity_status_to_do)

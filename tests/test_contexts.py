from pykechain.enums import ContextGroup, ContextType
# new in 1.13
from pykechain.models import Activity
from pykechain.models.context import Context
from tests.classes import TestBetamax


class TestContextSetup(TestBetamax):
    """Only for test setup, will create a context

    :ivar context: context
    """

    def setUp(self):
        super().setUp()
        self.context = self.client.create_context(
            name="__my first context for testing",
            context_type=ContextType.TIME_PERIOD, scope=self.project.id,
            tags=["testing"]
        )  # type: Context

    def tearDown(self):
        self.context.delete()
        super().tearDown()


class TestContextCreate(TestBetamax):
    def test_create_context(self):
        context = self.client.create_context(
            name="__my first context for testing",
            context_type=ContextType.TIME_PERIOD, scope=self.project, tags=["testing"]
        )
        self.assertTrue(context)
        self.assertSetEqual(set(context.tags), {"testing"})
        self.assertTrue(context.scope_id == self.project.id)
        self.assertEqual(context.name, "__my first context for testing")
        self.assertEqual(context.context_type, ContextType.TIME_PERIOD)

        # destroy
        context.delete()


class TestContexts(TestContextSetup):
    def test_retrieve_contexts_via_client_using_scope_filter(self):
        with self.subTest("via uuid"):
            contexts = self.client.contexts(scope=self.project.id)
            self.assertIsInstance(contexts[0], Context)

        with self.subTest("via Scope"):
            contexts = self.client.contexts(scope=self.project)
            self.assertIsInstance(contexts[0], Context)

        with self.subTest("via uuid string"):
            contexts = self.client.contexts(scope=str(self.project.id))
            self.assertIsInstance(contexts[0], Context)

    def test_retrieve_single_context_via_client_with_pk_filter(self):
        self.assertIsInstance(self.client.context(pk=self.context.id), Context)
        self.assertTrue(self.client.context(pk=self.context.id), Context)

    def test_create_contexts_bound_to_an_activity(self):
        task = self.project.create_activity("__Test task")
        self.assertIsInstance(task, Activity)
        self.context.link_activities(activities=[task])

        self.context.refresh()
        self.assertTrue(self.context.activities, [task])

    def test_retrieve_multiple_context_via_client_using_filters(self):
        contexts = self.client.contexts(context_type=ContextType.TIME_PERIOD)
        self.assertEqual(len(contexts), 1)

    def test_retrieve_multiple_contexts_via_client_using_group_filters(self):
        context_dept = self.client.create_context(
            name="a context1",
            context_type=ContextType.TEXT_LABEL,
            scope=self.project,
            context_group=ContextGroup.DEPARTMENT
        )
        context_asset = self.client.create_context(
            name="a context1",
            context_type=ContextType.TEXT_LABEL,
            scope=self.project,
            context_group=ContextGroup.ASSET
        )

        contexts = self.client.contexts(
            context_group__in=[ContextGroup.DEPARTMENT, ContextGroup.ASSET])
        self.assertSetEqual(set(contexts), {context_dept, context_asset})
        self.assertEqual(self.client.last_url, "asdasd")

        context_dept.delete()
        context_asset.delete()

    def test_link_context_to_activity(self):
        self.assertFalse(self.context.activities)
        self.context.link_activities(
            activities=[self.project.activity(name="Specify wheel diameter")])
        self.assertTrue(self.context.activities)

    def test_context_consequetive_link_many_activities(self):
        self.assertFalse(self.context.activities)
        self.context.link_activities(
            activities=[self.project.activity(name="Specify wheel diameter")])
        self.assertEqual(len(self.context.activities), 1)
        self.context.link_activities(activities=[self.project.activity(name="Task - Form")])
        self.assertEqual(len(self.context.activities), 2)

    def test_unlink_context_to_activity(self):
        self.assertFalse(self.context.activities)
        self.context.link_activities(
            activities=[self.project.activity(name="Specify wheel diameter")])
        self.assertTrue(self.context.activities)
        self.context.unlink_activities(
            activities=[self.project.activity(name="Specify wheel diameter")])
        self.assertFalse(self.context.activities)

    def test_context_unlink_single_activity_when_more_activities(self):
        self.assertFalse(self.context.activities)
        self.context.link_activities(
            activities=[
                self.project.activity(name="Specify wheel diameter"),
                self.project.activity(name="Task - Form")
            ]
        )
        self.assertEqual(len(self.context.activities), 2)
        self.context.unlink_activities(
            activities=[self.project.activity(name="Specify wheel diameter")])
        self.assertEqual(len(self.context.activities), 1)
        self.assertListEqual(list(self.context.activities),
                             [self.project.activity(name="Task - Form").id])

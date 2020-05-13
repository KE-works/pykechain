from unittest import TestCase

from pykechain.models import Activity2

from pykechain.exceptions import IllegalArgumentError
from pykechain.models.tags import TagsMixin
from tests.classes import TestBetamax


class TestTags(TestCase):
    tags = ['one', 'two', 'three']

    def setUp(self):
        self.obj = ConcreteTagsBase()
        self.obj._tags = self.tags

    def tearDown(self):
        pass

    def test_edit(self):
        self.assertIsNone(self.obj.edit(tags=self.tags))

    def test_getter(self):
        self.assertTrue(len(self.tags) == len(self.obj.tags))
        self.assertTrue(sorted(self.tags) == sorted(self.obj.tags))

    def test_setter(self):
        new_tags = ['1', '2', '3']
        self.obj.tags = new_tags

        self.assertTrue(len(new_tags) == len(self.obj.tags))
        self.assertTrue(sorted(new_tags) == sorted(self.obj.tags))

    def test_setter_duplicate(self):
        self.obj.add_tag(tag='one')
        self.assertTrue(len(self.obj.tags) == 3)

    def test_setter_none(self):
        self.obj.tags = None

        self.assertIsInstance(self.obj.tags, list)
        self.assertTrue(len(self.obj.tags) == 0)

    def test_setter_not_an_iterable(self):
        with self.assertRaises(IllegalArgumentError):
            self.obj.tags = 'four'

    def test_setter_not_a_string(self):
        with self.assertRaises(ValueError):
            self.obj.tags = [1, 2, 3]

    def test_remove_tag(self):
        self.obj.remove_tag(tag='two')

        self.assertNotIn('two', self.obj.tags)

    def test_remove_tag_failure(self):
        with self.assertRaises(IllegalArgumentError):
            self.obj.remove_tag(tag='just a flesh wound')

    def test_add_tag(self):
        self.obj.add_tag(tag='four')

        self.assertIn('four', self.obj.tags)

    def test_has_tag_true(self):
        self.assertTrue(self.obj.has_tag(tag='three'))

    def test_has_tag_false(self):
        self.assertFalse(self.obj.has_tag(tag='ten'))


class TestTagsScope(TestBetamax):

    def test_scope_tags(self):
        """test to retrieve the tags for a scope"""
        # setup
        saved_tags = self.project.tags

        # test
        scope_tags = ['a', 'list', 'of-tags']
        self.project.edit(tags=scope_tags)
        self.assertListEqual(scope_tags, self.project.tags)

        self.assertTrue(len(scope_tags) == len(self.project.tags))
        self.assertTrue(sorted(scope_tags) == sorted(self.project.tags))

        # teardown
        self.project.edit(tags=saved_tags)

    def test_scope_tags_may_be_emptied(self):
        # setup
        saved_tags = self.project.tags

        # test
        self.project.edit(tags=[])
        self.assertListEqual(self.project.tags, [])

        # teardown
        self.project.edit(tags=saved_tags)


class TestTagsActivity(TestBetamax):
    tags = ['one', 'two', 'three']

    def setUp(self):
        super(TestTagsActivity, self).setUp()
        self.task = self.project.activity(name='SubTask')  # type: Activity2

    def tearDown(self):
        self.task.tags = None
        super(TestTagsActivity, self).tearDown()

    def test_activity_tags(self):
        # setup
        new_tags = ['four', 'five', 'six']
        self.task.tags = new_tags
        reloaded = self.project.activity(pk=self.task.id)

        self.assertEqual(len(new_tags), len(reloaded.tags))
        self.assertListEqual(sorted(new_tags), sorted(reloaded.tags))

    def test_activity_tags_may_be_emptied(self):
        # setup
        self.task.tags = []
        reloaded_task = self.project.activity(pk=self.task.id)

        self.assertEqual(0, len(reloaded_task.tags))


class ConcreteTagsBase(TagsMixin):
    """
    Dummy implementation of the edit method allows for instantiation of the TagsMixin class.
    """

    def edit(self, tags=None, *args, **kwargs):
        return None

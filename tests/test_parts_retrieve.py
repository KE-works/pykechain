from pykechain.enums import Category, Multiplicity
from pykechain.exceptions import NotFoundError, MultipleFoundError, IllegalArgumentError
from pykechain.models import PartSet, Part2
from pykechain.utils import find
from tests.classes import TestBetamax


class TestPartRetrieve(TestBetamax):
    # 1.8
    def test_get_instances_of_a_model(self):
        wheel_model = self.project.model('Wheel')
        wheel_instances = wheel_model.instances()

        self.assertIsInstance(wheel_instances, PartSet)
        for wheel_instance in wheel_instances:
            self.assertEqual(wheel_instance.category, Category.INSTANCE)
            self.assertEqual(wheel_instance.model().id, wheel_model.id)

    def test_get_instances_of_an_instances_raises_notfound(self):
        wheel_instance = self.project.part('Rear Wheel', category=Category.INSTANCE)
        with self.assertRaises(NotFoundError):
            wheel_instance.instances()

    def test_get_single_instance_of_a_model(self):
        bike_model = self.project.model('Bike')
        bike_instance = bike_model.instance()

        self.assertEqual(bike_instance.category, Category.INSTANCE)

    def test_get_single_instance_of_a_multiplicity_model_raises_multiplefounderror(self):
        wheel_model = self.project.model('Wheel')

        with self.assertRaises(MultipleFoundError):
            wheel_model.instance()

    # test added in 1.12.7
    def test_get_single_instance_of_a_model_without_instances_raises_notfounderror(self):
        catalog = self.project.model(name__startswith='Catalog')
        model_without_instances = self.project.create_model(parent=catalog, name='model_without_instances',
                                                            multiplicity=Multiplicity.ZERO_ONE)

        with self.assertRaises(NotFoundError):
            model_without_instances.instance()

        # tearDown
        model_without_instances.delete()

    # test added in 2.1, changed in 3.2
    def test_get_parts_with_descendants_tree(self):
        # setUp
        root = self.project.part(name='Product')
        root.populate_descendants()

        # testing
        self.assertIsInstance(root._cached_children, list)
        self.assertEqual(1, len(root._cached_children), msg='Number of instances has changed, expected 1')

        # follow-up
        bike_part = find(root._cached_children, lambda d: d.name == 'Bike')
        self.assertIsNotNone(bike_part._cached_children)
        self.assertEqual(7, len(bike_part._cached_children), msg='Number of child instances has changed, expected 7')

    # test added in 2.1, changed in 3.2
    def test_get_models_with_descendants_tree(self):
        # setUp
        root = self.project.model(name='Product')
        root.populate_descendants()

        # testing
        self.assertIsInstance(root._cached_children, list)
        self.assertEqual(1, len(root._cached_children), msg='Number of models has changed, expected 1')

        # follow-up
        bike_model = find(root._cached_children, lambda d: d.name == 'Bike')
        self.assertIsNotNone(bike_model._cached_children)
        self.assertEqual(5, len(bike_model._cached_children), msg='Number of child models has changed, expected 5')

    # test added in 3.0
    def test_retrieve_parts_with_refs(self):
        # setup
        front_fork_ref = 'front-fork'
        front_fork_name = 'Front Fork'
        front_fork_part = self.project.part(ref=front_fork_ref)
        front_fork_model = self.project.model(ref=front_fork_ref)

        # testing
        self.assertIsInstance(front_fork_part, Part2)
        self.assertEqual(front_fork_name, front_fork_part.name)
        self.assertEqual(Category.INSTANCE, front_fork_part.category)

        self.assertIsInstance(front_fork_model, Part2)
        self.assertEqual(front_fork_name, front_fork_model.name)
        self.assertEqual(Category.MODEL, front_fork_model.category)

    def test_child(self):
        root = self.project.model(name='Product')

        bike = root.child(name='Bike')

        self.assertIsInstance(bike, Part2)
        self.assertEqual(bike.parent_id, root.id)

        bike_via_call = root('Bike')

        self.assertEqual(bike, bike_via_call)

        with self.assertRaises(IllegalArgumentError):
            root.child()

    def test_all_children(self):
        root = self.project.model(name='Product')

        all_children = root.all_children()

        self.assertIsInstance(all_children, list)
        self.assertEqual(6, len(all_children), msg='Number of models has changed, expected 6')

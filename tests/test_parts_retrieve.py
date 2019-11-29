from pykechain.enums import Category, Multiplicity
from pykechain.exceptions import NotFoundError, MultipleFoundError
from pykechain.models import PartSet, Part2
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

    # test added in 2.1
    def test_get_parts_with_descendants_tree(self):
        # setUp
        bike_part = self.project.part(name='Bike')
        bike_part.populate_descendants()
        bike_model = self.project.model(name='Bike')
        bike_model.populate_descendants()
        # testing
        self.assertTrue(len(bike_part._cached_children) >= 5)
        self.assertTrue(len(bike_model._cached_children) >= 4)

    # test added in 3.0
    def test_retrieve_parts_with_refs(self):
        # setup
        front_fork_ref = 'front-fork'
        front_fork_name = 'Front fork'
        front_fork_part = self.project.part(ref=front_fork_ref)
        front_fork_model = self.project.model(ref=front_fork_ref)

        # testing
        self.assertIsInstance(front_fork_part, Part2)
        self.assertTrue(front_fork_part.name, front_fork_name)
        self.assertTrue(front_fork_part.category, Category.INSTANCE)

        self.assertIsInstance(front_fork_model, Part2)
        self.assertTrue(front_fork_model.name, front_fork_name)
        self.assertTrue(front_fork_model.category, Category.MODEL)

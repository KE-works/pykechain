from unittest import skipIf

from pykechain.enums import Multiplicity, Category, Classification
from pykechain.exceptions import NotFoundError, MultipleFoundError, APIError, IllegalArgumentError
from pykechain.models import PartSet, Part2
from tests.classes import TestBetamax
from tests.utils import TEST_FLAG_IS_PIM3


class TestParts(TestBetamax):

    def setUp(self):
        super().setUp()
        self._part = None

    def tearDown(self):
        if self._part:
            self._part.delete()
        super().tearDown()

    def test_retrieve_parts(self):
        parts = self.project.parts()

        # Check if there are parts
        self.assertTrue(len(parts))
        self.assertIsInstance(parts[0], Part2)

    def test_retrieve_single_part(self):
        part_to_retrieve = self.project.parts()[0]
        part = self.project.part(part_to_retrieve.name)

        self.assertTrue(part)

    def test_base_comparison(self):
        all_parts = self.project.parts()

        tip = ' See Base.__eq__() method.'
        self.assertFalse(all_parts[0] == all_parts[1], msg='2 different parts must not be equal.' + tip)
        self.assertTrue(all_parts[0] == all_parts[0], msg='The same part must be equal.' + tip)
        self.assertFalse(all_parts[0] == 5, msg='A part must not be equal to a non-pykechain object.' + tip)

    def test_base_hash(self):
        wheel = self.project.model('Wheel')
        a_dict = dict()

        try:
            a_dict[wheel] = 3
        except TypeError:
            self.assertTrue(False, msg='Parts must be hashable See Base.__hash__() method.')

    def test_part_attributes(self):
        attributes = ['_client', '_json_data', 'id', 'name', 'created_at', 'updated_at', 'ref',
                      'category', 'classification', 'parent_id', 'description', 'multiplicity',
                      '_cached_children', 'properties']

        obj = self.project.parts(limit=1)[0]
        for attribute in attributes:
            with self.subTest(msg=attribute):
                self.assertTrue(hasattr(obj, attribute), "Could not find '{}' in the object: '{}'".format(
                    attribute, obj.__dict__.keys()))

    def test_retrieve_single_unknown(self):
        with self.assertRaises(NotFoundError):
            self.project.part('123lladadwd')

    def test_retrieve_single_multiple(self):
        with self.assertRaises(MultipleFoundError):
            self.project.part()

    def test_retrieve_models(self):
        wheel = self.project.model('Wheel')

        self.assertTrue(self.project.parts(model=wheel))

    def test_retrieve_model_unknown(self):
        with self.assertRaises(NotFoundError):
            self.client.model('123lladadwd')

    def test_retrieve_model_multiple(self):
        with self.assertRaises(MultipleFoundError):
            self.project.model()

    def test_scope(self):
        first_part = self.project.parts()[0]

        self.assertEqual(first_part.scope(), self.project)

    def test_part_set_iterator(self):
        for part in self.project.parts():
            self.assertTrue(part.name)

    def test_part_set_get_item_invalid(self):
        part_set = self.project.parts()

        with self.assertRaises(NotImplementedError):
            # noinspection PyStatementEffect
            part_set['testing']

    def test_wrongly_create_model(self):
        # setUp
        bike_model = self.project.model(name='Bike')

        # testing
        with self.assertRaises(IllegalArgumentError):
            self.client.create_model(name='Multiplicity does not exist', parent=bike_model, multiplicity='TEN')

    def test_part_add_delete_part(self):
        bike = self.project.part('Bike')
        wheel_model = self.project.model('Wheel')

        wheel = bike.add(wheel_model, name='Test Wheel')
        wheel.delete()

        wheel = wheel_model.add_to(bike)
        wheel.delete()

        with self.assertRaises(APIError):
            bike.delete()

    def test_create_part_where_parent_is_model(self):
        # setUp
        bike_model = self.project.model(name='Bike')

        # testing
        with self.assertRaises(IllegalArgumentError):
            self._part = self.client.create_part(name='Parent should be instance',
                                                 parent=bike_model, model=bike_model)

    def test_create_part_where_model_is_instance(self):
        # setUp
        bike_instance = self.project.part(name='Bike')

        # testing
        with self.assertRaises(IllegalArgumentError):
            self._part = self.client.create_part(name='Model should not be instance',
                                                 parent=bike_instance, model=bike_instance)

    def test_create_model_where_parent_is_instance(self):
        # setUp
        bike_instance = self.project.part(name='Bike')

        # testing
        with self.assertRaises(IllegalArgumentError):
            self._part = self.client.create_model(name='Parent should be model',
                                                  parent=bike_instance, multiplicity=Multiplicity.ONE)

    def test_create_proxy_model_where_model_is_instance(self):
        # setUp
        bike_instance = self.project.part(name='Bike')

        # testing
        with self.assertRaises(IllegalArgumentError):
            self._part = self.client.create_proxy_model(name='Model should not be instance',
                                                        model=bike_instance, parent=bike_instance)

    def test_create_proxy_model_where_parent_is_instance(self):
        # setUp
        bike_instance = self.project.part(name='Bike')
        bike_model = self.project.model(name='Bike')

        # testing
        with self.assertRaises(IllegalArgumentError):
            self._part = self.client.create_proxy_model(name='Parent should not be instance',
                                                        model=bike_model, parent=bike_instance)

    def test_add_to_wrong_categories(self):
        # This test has the purpose of testing of whether APIErrors are raised when illegal operations are
        # performed (e.g. operation that should be performed on part instances but instead are being performed
        # on part models and vice versa)
        project = self.project

        bike_model = project.model('Bike')
        bike_instance = project.part('Bike')
        wheel_model = project.model('Wheel')

        with self.assertRaises(APIError):
            self._part = bike_model.add(wheel_model)

        front_fork_instance = project.part('Front Fork')

        with self.assertRaises(APIError):
            self._part = front_fork_instance.add_to(bike_instance)

        with self.assertRaises(APIError):
            self._part = bike_instance.add_model('Engine')

        with self.assertRaises(APIError):
            self._part = bike_instance.add_property('Electrical Power')

        with self.assertRaises(APIError):
            self._part = bike_model.add_with_properties(wheel_model)

    def test_part_html_table(self):
        part = self.project.part('Front Wheel')

        self.assertIn("</table>", part._repr_html_())

    def test_part_set_html_table(self):
        parts = self.project.parts()

        self.assertIn("</table>", parts._repr_html_())

    def test_part_set_html_categories(self):
        parts = self.project.parts(category=None)

        self.assertIn("<th>Category</th>", parts._repr_html_())

    # version 1.1.2 and later
    def test_part_set_with_limit(self):
        limit = 5
        parts = self.project.parts(limit=limit)

        self.assertEqual(len(parts), limit)

    def test_part_set_with_batch(self):
        batch = 5
        parts = self.project.parts(batch=batch)
        self.assertTrue(len(parts) >= batch)

    # version 1.1.3 and later
    def test_retrieve_parent_of_part(self):
        frame = self.project.part('Frame')  # type: Part2
        self.assertTrue(hasattr(frame, 'parent_id'))
        parent_of_frame = frame.parent()
        self.assertIsInstance(parent_of_frame, type(frame))

    def test_retrieve_children_of_part(self):
        bike = self.project.part('Bike')  # type: Part2
        self.assertIsInstance(bike, Part2)
        children_of_bike = bike.children()
        self.assertIsInstance(children_of_bike, (PartSet, list))
        self.assertTrue(len(children_of_bike) >= 1)  # eg. Wheels ...

    def test_retrieve_siblings_of_part(self):
        """Test if the siblings of a part is the same as the children of the parent of the part"""
        frame = self.project.part('Frame')  # type: Part2
        siblings_of_frame = frame.siblings()
        self.assertIsInstance(siblings_of_frame, PartSet)
        self.assertTrue(len(siblings_of_frame) >= 1)  # eg. Wheels ...

        # double check that the children of the parent of frame are the same as the siblings of frame
        children_of_parent_of_frame = frame.parent().children()  # type: PartSet
        self.assertEqual(len(children_of_parent_of_frame), len(siblings_of_frame))
        children_of_parent_of_frame_ids = [p.id for p in children_of_parent_of_frame]
        for sibling in siblings_of_frame:
            self.assertIn(sibling.id, children_of_parent_of_frame_ids,
                          'sibling {} is appearing in the siblings method and not in the children of '
                          'parent method'.format(sibling))

    # new in 1.3+
    def test_kwargs_on_part_retrieval(self):
        # test that the additional kwargs are added to the query filter on the api
        bikes = self.project.parts('Bike', order=True)  # type:PartSet
        self.assertTrue(len(bikes) == 1)
        self.assertTrue(self.client.last_url.find('order'))

    # new in 1.5+
    def test_edit_part_instance_name(self):
        front_fork = self.project.part('Front Fork')
        front_fork_old_name = str(front_fork.name)
        front_fork.edit(name='Front Fork - updated')

        front_fork_updated = self.project.part('Front Fork - updated')
        self.assertEqual(front_fork.id, front_fork_updated.id)
        self.assertEqual(front_fork.name, front_fork_updated.name)
        self.assertEqual(front_fork.name, 'Front Fork - updated')

        with self.assertRaises(IllegalArgumentError):
            front_fork.edit(name=True)

        # teardown
        front_fork.edit(name=front_fork_old_name)

    def test_edit_part_instance_description(self):
        front_fork = self.project.part('Front Fork')
        front_fork_old_description = str(front_fork._json_data.get('description'))
        front_fork.edit(description='A normal Front Fork')

        front_fork_updated = self.project.part('Front Fork')
        self.assertEqual(front_fork.id, front_fork_updated.id)

        with self.assertRaises(IllegalArgumentError):
            front_fork.edit(description=42)

        # teardown
        front_fork.edit(description=front_fork_old_description)

    def test_edit_part_model_name(self):
        front_fork = self.project.model('Front Fork')
        front_fork_oldname = str(front_fork.name)
        front_fork.edit(name='Front Fork - updated')

        front_fork_updated = self.project.model('Front Fork - updated')
        self.assertEqual(front_fork.id, front_fork_updated.id)
        self.assertEqual(front_fork.name, front_fork_updated.name)

        # teardown
        front_fork.edit(name=front_fork_oldname)

    def test_create_model(self):
        bike = self.project.model('Bike')
        pedal = self.project.create_model(bike, 'Pedal', multiplicity=Multiplicity.ONE)
        self._part = pedal
        pedal_model = self.project.model('Pedal')

        self.assertTrue(pedal.id, pedal_model.id)
        self.assertTrue(pedal._json_data['multiplicity'], 'ONE')

    def test_add_proxy_to(self):
        catalog_container = self.project.model(name__startswith='Catalog')
        bearing_catalog_model = catalog_container.add_model('Bearing', multiplicity=Multiplicity.ZERO_MANY)
        wheel_model = self.project.model('Wheel')

        bearing_proxy_model = bearing_catalog_model.add_proxy_to(wheel_model, 'Bearing', Multiplicity.ZERO_ONE)

        self.assertTrue(bearing_proxy_model.category, Category.MODEL)
        self.assertTrue(bearing_proxy_model.parent(), wheel_model)

        # teardown
        all_bearing_proxies = self.project.parts(name='Bearing', category=Category.MODEL, parent=wheel_model.id)
        self.assertGreaterEqual(len(all_bearing_proxies), 1)
        for bearing_proxy in all_bearing_proxies:
            bearing_proxy.delete()

        all_bearing_catalog_models = self.project.parts(name='Bearing', category=Category.MODEL)
        self.assertGreaterEqual(len(all_bearing_catalog_models), 1)
        for bearing_catalog_model in all_bearing_catalog_models:
            bearing_catalog_model.delete()

        all_bearing_models = self.project.parts(name='Bearing', category=Category.MODEL)
        self.assertEqual(len(all_bearing_models), 0)

    # new in 1.6
    def test_retrieve_model(self):
        front_fork = self.project.part('Front Fork')
        front_fork_model = self.project.model('Front Fork')

        front_fork_retrieved_model = front_fork.model()

        # Added to improve coverage. Assert whether NotFoundError is raised when model() method is applied to
        # a part that has no model
        with self.assertRaises(NotFoundError):
            front_fork_model.model()

        self.assertEqual(front_fork_model.id, front_fork_retrieved_model.id)

    def test_retrieve_catalog_model_of_proxy(self):
        catalog_container = self.project.model(name__startswith='Catalog')
        bearing_catalog_model = catalog_container.add_model('Bearing', multiplicity=Multiplicity.ZERO_MANY)
        wheel_model = self.project.model('Wheel')

        # add proxy model to product Bike > Wheel based on catalog model 'Bearing'
        bearing_proxy_model = bearing_catalog_model.add_proxy_to(wheel_model, 'Bearing', Multiplicity.ZERO_ONE)

        self.assertTrue(bearing_proxy_model.category, Category.MODEL)
        self.assertTrue(bearing_proxy_model.parent(), wheel_model)

        # the call to test here
        re_retrieved_bearing_catalog_model = self.project.model('Bearing', classification=Classification.CATALOG)
        self.assertEqual(bearing_catalog_model, re_retrieved_bearing_catalog_model)

        # teardown
        all_bearing_proxies = self.project.parts(name='Bearing', category=Category.MODEL, parent=wheel_model.id)
        self.assertGreaterEqual(len(all_bearing_proxies), 1)
        for bearing_proxy in all_bearing_proxies:
            bearing_proxy.delete()

        all_bearing_catalog_models = self.project.parts(name='Bearing', category=Category.MODEL)
        self.assertGreaterEqual(len(all_bearing_catalog_models), 1)
        for bearing_catalog_model in all_bearing_catalog_models:
            bearing_catalog_model.delete()

        all_bearing_models = self.project.parts(name='Bearing', category=Category.MODEL)
        self.assertEqual(len(all_bearing_models), 0)

    def test_retrieve_non_existent_proxies_of_a_catalog_model_raises_error(self):
        # Added to improve coverage. Assert whether NotFoundError is raised when proxy_model() method is applied to
        # a part that is not a proxy
        catalog_model = self.project.model('Model', classification=Classification.CATALOG)
        with self.assertRaises(NotFoundError):
            catalog_model.proxy_model()

    def test_retrieve_proxy_of_instance(self):
        instance = self.project.part('Rear Wheel')

        with self.assertRaises(IllegalArgumentError):
            instance.proxy_model()

    # new in 1.8+
    def test_retrieve_part_multiplicity(self):
        bike_model = self.project.model('Bike')
        self.assertEqual(bike_model.multiplicity, Multiplicity.ONE_MANY, bike_model.multiplicity)

    # new in 1.9
    def test_retrieve_part_properties_in_a_dict(self):
        # Retrieve the bike part
        bike = self.project.part('Bike')

        # Call the function to be tested
        bike_properties = bike.as_dict()

        # Check whether bike_properties contains all the property names in bike
        for prop in bike.properties:
            self.assertTrue(prop.name in bike_properties)

    # new in 1.12
    def test_retrieve_children_of_part_with_additional_arguments(self):
        bike = self.project.part('Bike')  # type: Part2
        self.assertIsInstance(bike, Part2)
        children_of_bike = bike.children(name__icontains='Wheel')
        self.assertIsInstance(children_of_bike, PartSet)
        self.assertTrue(len(children_of_bike) >= 1)  # eg. Wheels ...

    def test_retrieve_siblings_of_part_with_additional_arguments(self):
        """Test if the siblings of a part is the same as the children of the parent of the part"""
        frame = self.project.part('Frame')  # type: Part2
        siblings_of_frame = frame.siblings(name__icontains='Wheel')
        self.assertIsInstance(siblings_of_frame, PartSet)
        self.assertTrue(len(siblings_of_frame) >= 1)  # eg. Wheels ...

    # new in 2.3
    def test_clone_model(self):
        # setUp
        model_name = 'Seat'
        seat = self.project.model(model_name)
        self._part = seat.clone()

        # testing
        clone_seat_model = self.project.model('CLONE - {}'.format(model_name))
        self.assertTrue(clone_seat_model)

    def test_clone_instance(self):
        instance_name = 'Front Wheel'
        wheel = self.project.part(instance_name)
        self._part = wheel.clone()

        # testing
        clone_spoke_instance = self.project.part('CLONE - {}'.format(instance_name))
        self.assertTrue(clone_spoke_instance)

    def test_clone_instance_with_multiplicity_violation(self):
        instance_name = 'Seat'
        seat = self.project.part(instance_name)

        seat_model = seat.model()

        # testing
        self.assertEqual(Multiplicity.ONE, seat_model.multiplicity)
        with self.assertRaises(APIError):
            self._part = seat.clone()


@skipIf(not TEST_FLAG_IS_PIM3, reason="This tests is designed for PIM version 3, expected to fail on older PIM3")
class TestPIM2SpecificPartTests(TestBetamax):
    """Pim3 capable tests."""

    def test_retrieve_part_without_parent_id(self):
        # only the root does not have a parent_id
        product_root_node = self.project.part(name='Product', classification=Classification.PRODUCT)
        self.assertTrue(hasattr(product_root_node, 'parent_id'))
        self.assertIsNotNone(product_root_node.parent_id)
        self.assertIsNone(product_root_node.parent().parent_id)

    def test_retrieve_parent_of_part_without_parent_id(self):
        # only the root does not have a parent_id
        product_root_node = self.project.part(name='Product', classification=Classification.PRODUCT)
        root_node = product_root_node.parent()
        self.assertEqual(root_node.name, "Root")
        self.assertIsNone(root_node.parent())

    def test_retrieve_siblings_of_part_without_parent_id(self):
        product_root_node = self.project.part(name='Product', classification=Classification.PRODUCT)
        siblings_of_product_root_node = product_root_node.siblings()
        self.assertIsInstance(siblings_of_product_root_node, PartSet)
        self.assertEqual(len(siblings_of_product_root_node), 2)

        siblings_of_root_node = product_root_node.parent().siblings()
        self.assertIsInstance(siblings_of_root_node, PartSet)
        self.assertEqual(len(siblings_of_root_node), 0)

from pykechain.enums import Multiplicity, Category
from pykechain.exceptions import NotFoundError, MultipleFoundError, APIError
from pykechain.models import Part, PartSet
from tests.classes import TestBetamax


class TestParts(TestBetamax):
    def test_retrieve_parts(self):
        parts = self.project.parts()

        # Check if there are parts
        assert len(parts)

    def test_retrieve_single_part(self):
        part = self.project.part('Front Wheel')

        assert part

    def test_retrieve_single_unknown(self):
        with self.assertRaises(NotFoundError):
            self.project.part('123lladadwd')

    def test_retrieve_single_multiple(self):
        with self.assertRaises(MultipleFoundError):
            self.project.part()

    def test_retrieve_models(self):
        project = self.client.scope('Bike Project')
        wheel = project.model('Wheel')

        assert project.parts(model=wheel)

    def test_retrieve_model_unknown(self):
        with self.assertRaises(NotFoundError):
            self.client.model('123lladadwd')

    def test_retrieve_model_multiple(self):
        with self.assertRaises(MultipleFoundError):
            self.client.model()

    def test_part_set_iterator(self):
        for part in self.project.parts():
            assert part.name

    def test_part_set_get_item_invalid(self):
        part_set = self.project.parts()

        with self.assertRaises(NotImplementedError):
            part_set['testing']

    def test_part_add_delete_part(self):
        project = self.client.scope('Bike Project')

        bike = project.part('Bike')
        wheel_model = project.model('Wheel')

        wheel = bike.add(wheel_model, name='Test Wheel')
        wheel.delete()

        wheel = wheel_model.add_to(bike)
        wheel.delete()

        with self.assertRaises(APIError):
            bike.delete()

    def test_part_html_table(self):
        part = self.project.part('Front Wheel')

        assert "</table>" in part._repr_html_()

    def test_part_set_html_table(self):
        parts = self.project.parts()

        assert "</table>" in parts._repr_html_()

    def test_part_set_html_categories(self):
        parts = self.project.parts(category=None)

        assert "<th>Category</th>" in parts._repr_html_()

    # version 1.1.2 and later
    def test_part_set_with_limit(self):
        limit = 5
        parts = self.project.parts(limit=limit)

        assert len(parts) == limit

    def test_part_set_with_batch(self):
        batch = 5
        parts = self.project.parts(batch=batch)
        assert len(parts) >= batch

    # version 1.1.3 and later
    def test_retrieve_parent_of_part(self):
        frame = self.project.part('Frame')  # type:Part
        assert hasattr(frame, 'parent_id')
        parent_of_frame = frame.parent()
        assert type(parent_of_frame) is type(frame)

    def test_retrieve_children_of_part(self):
        bike = self.project.part('Bike')  # type:Part
        assert type(bike) is Part
        children_of_bike = bike.children()
        assert type(children_of_bike) is PartSet
        assert len(children_of_bike) >= 1  # eg. Wheels ...

    def test_retrieve_siblings_of_part(self):
        """Test if the siblings of a part is the same as the children of the parent of the part"""
        frame = self.project.part('Frame')  # type:Part
        siblings_of_frame = frame.siblings()
        assert type(siblings_of_frame) is PartSet
        assert len(siblings_of_frame) >= 1  # eg. Wheels ...

        # double check that the children of the parent of frame are the same as the siblings of frame
        children_of_parent_of_frame = frame.parent().children()  # type: PartSet
        assert len(children_of_parent_of_frame) == len(siblings_of_frame)
        children_of_parent_of_frame_ids = [p.id for p in children_of_parent_of_frame]
        for sibling in siblings_of_frame:
            assert sibling.id in children_of_parent_of_frame_ids, \
                'sibling {} is appearing in the siblings method and not in the children of ' \
                'parent method'.format(sibling)

    def test_retrieve_part_without_parent_id(self):
        # only the root does not have a parent_id
        ROOT_NODE_ID = 'f521333e-a1ed-4e65-b166-999f91a38cf1'
        root_node = self.project.part(pk=ROOT_NODE_ID)  # type: Part
        assert hasattr(root_node, 'parent_id')
        assert root_node.parent_id == None

    def test_retrieve_parent_of_part_without_parent_id(self):
        # only the root does not have a parent_id
        ROOT_NODE_ID = 'f521333e-a1ed-4e65-b166-999f91a38cf1'
        root_node = self.project.part(pk=ROOT_NODE_ID)  # type: Part
        parent_of_rootnode = root_node.parent()
        assert parent_of_rootnode is None

    def test_retrieve_siblings_of_part_without_parent_id(self):
        ROOT_NODE_ID = 'f521333e-a1ed-4e65-b166-999f91a38cf1'
        root_node = self.project.part(pk=ROOT_NODE_ID)  # type: Part
        siblings_of_root_node = root_node.siblings()
        assert type(siblings_of_root_node) is PartSet
        assert len(siblings_of_root_node) is 0

    # new in 1.3+
    def test_kwargs_on_part_retrieval(self):
        # test that the additional kwargs are added to the query filter on the api
        bikes = self.project.parts('Bike', descendants=True)  # type:Part
        assert len(bikes) > 1
        assert self.client.last_url.find('descendants')

    # new in 1.5+
    def test_edit_part_instance_name(self):
        front_fork = self.project.part('Front Fork')
        front_fork.edit(name='Front Fork - updated')

        front_fork_u = self.project.part('Front Fork - updated')
        assert front_fork.id == front_fork_u.id
        assert front_fork.name == front_fork_u.name
        assert front_fork.name == 'Front Fork - updated'

        front_fork.edit(name='Front Fork')

    def test_edit_part_instance_description(self):
        front_fork = self.project.part('Front Fork')
        front_fork.edit(description='A normal Front Fork')

        front_fork_u = self.project.part('Front Fork')
        assert front_fork.id == front_fork_u.id

        front_fork.edit(description='A perfectly normal Front Fork')

    def test_edit_part_model_name(self):
        front_fork = self.project.model('Front Fork')
        front_fork.edit(name='Front Fork - updated')

        front_fork_u = self.project.model('Front Fork - updated')
        assert front_fork.id == front_fork_u.id
        assert front_fork.name == front_fork_u.name

        front_fork.edit(name='Front Fork')

    def test_new_proxy_model(self):
        catalog_container = self.project.model('Catalog container')
        bearing_catalog_model = catalog_container.add_model('Bearing', multiplicity=Multiplicity.ZERO_MANY)
        wheel_model = self.project.model('Wheel')

        bearing_proxy_model = self.client.create_proxy_model(
            bearing_catalog_model, wheel_model, 'Bearing', Multiplicity.ZERO_ONE)

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

        front_fork_retrieved_model = front_fork.get_model()

        assert front_fork_model.id == front_fork_retrieved_model.id


class TestPartUpdate(TestBetamax):
    def test_part_update_with_dictionary(self):
        # setup
        front_fork = self.project.part('Front Fork')  # type: Part
        saved_front_fork_properties = dict([(p.name, p.value) for p in front_fork.properties])

        # do tests
        update_dict = {
            'Material': 'Unobtanium',
            'Height (mm)': 123.4,
            'Color': 'Space Grey (old)'
        }
        front_fork.update(update_dict)
        refreshed_front_fork = self.project.part(pk=front_fork.id)
        for prop in refreshed_front_fork.properties:
            assert prop.name in update_dict, "property with {} should be in the update dict".format(prop.name)
            assert update_dict[prop.name] == prop.value, "property {} with value {} did not match contents " \
                                                         "with KEC".format(prop.name, prop.value)

        # tearDown
        for prop_name, prop_value in saved_front_fork_properties.items():
            front_fork.property(prop_name).value = prop_value

    def test_part_update_with_missing_property(self):
        # setup
        front_fork = self.project.part('Front Fork')  # type: Part
        saved_front_fork_properties = dict([(p.name, p.value) for p in front_fork.properties])

        # do tests
        update_dict = {
            'Unknown Property': 'Woot!'
        }
        with self.assertRaises(NotFoundError):
            front_fork.update(update_dict)

        # tearDown
        for prop_name, prop_value in saved_front_fork_properties.items():
            front_fork.property(prop_name).value = prop_value


class TestPartCreateWithProperties(TestBetamax):
    def test_create_part_with_properties_no_bulk(self):
        """Test create a part with the properties when bulk = False for old API compatibility"""
        parent = self.project.part('Bike')  # type: Part
        wheel_model = self.project.model('Wheel')  # type: Part

        update_dict = {
            'Diameter': 42.42,
            'Spokes': 42,
            'Rim Material': 'Unobtanium'
        }

        new_wheel = parent.add_with_properties(wheel_model, "Fresh Wheel", update_dict=update_dict, bulk=False)

        self.assertEqual(type(new_wheel), Part)
        self.assertTrue(new_wheel.property('Diameter'), 42.42)

        new_wheel.delete()

    def test_create_part_with_properties_with_bulk(self):
        """Test create a part with the properties when bulk = False for old API compatibility"""
        parent = self.project.part('Bike')  # type: Part
        wheel_model = self.project.model('Wheel')  # type: Part

        update_dict = {
            'Diameter': 42.43,
            'Spokes': 42,
            'Rim Material': 'Unobtanium'
        }

        new_wheel = parent.add_with_properties(wheel_model, "Fresh Wheel", update_dict=update_dict, bulk=True)

        self.assertEqual(type(new_wheel), Part)
        self.assertTrue(new_wheel.property('Diameter'), 42.43)

        new_wheel.delete()

from pykechain.enums import Multiplicity, Category
from pykechain.exceptions import NotFoundError, MultipleFoundError, APIError, IllegalArgumentError
from pykechain.models import Part, PartSet
from tests.classes import TestBetamax


class TestParts(TestBetamax):
    def test_retrieve_parts(self):
        parts = self.project.parts()

        # Check if there are parts
        self.assertTrue(len(parts))

    def test_retrieve_single_part(self):
        part = self.project.part('Front Wheel')

        self.assertTrue(part)

    def test_retrieve_single_unknown(self):
        with self.assertRaises(NotFoundError):
            self.project.part('123lladadwd')

    def test_retrieve_single_multiple(self):
        with self.assertRaises(MultipleFoundError):
            self.project.part()

    def test_retrieve_models(self):
        project = self.client.scope('Bike Project (pykechain testing)')
        wheel = project.model('Wheel')

        self.assertTrue(project.parts(model=wheel))

    def test_retrieve_model_unknown(self):
        with self.assertRaises(NotFoundError):
            self.client.model('123lladadwd')

    def test_retrieve_model_multiple(self):
        with self.assertRaises(MultipleFoundError):
            self.client.model()

    def test_part_set_iterator(self):
        for part in self.project.parts():
            self.assertTrue(part.name)

    def test_part_set_get_item_invalid(self):
        part_set = self.project.parts()

        with self.assertRaises(NotImplementedError):
            part_set['testing']

    def test_part_add_delete_part(self):
        project = self.client.scope('Bike Project (pykechain testing)')

        bike = project.part('Bike')
        wheel_model = project.model('Wheel')

        wheel = bike.add(wheel_model, name='Test Wheel')
        wheel.delete()

        wheel = wheel_model.add_to(bike)
        wheel.delete()

        with self.assertRaises(APIError):
            bike.delete()

    def test_add_to_wrong_categories(self):
        # This test has the purpose of testing of whether APIErrors are raised when illegal operations are
        # performed (e.g. operation that should be performed on part instances but instead are being performed
        # on part models and vice versa)
        project = self.client.scope('Bike Project (pykechain testing)')

        bike_model = project.model('Bike')
        bike_instance = project.part('Bike')
        wheel_model = project.model('Wheel')

        with self.assertRaises(APIError):
            bike_model.add(wheel_model)

        front_fork_instance = project.part('Front Fork')

        with self.assertRaises(APIError):
            front_fork_instance.add_to(bike_instance)

        with self.assertRaises(APIError):
            bike_instance.add_model('Engine')

        with self.assertRaises(APIError):
            bike_instance.add_property('Electrical Power')

        with self.assertRaises(APIError):
            bike_model.add_with_properties(wheel_model)

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
        frame = self.project.part('Frame')  # type:Part
        self.assertTrue(hasattr(frame, 'parent_id'))
        parent_of_frame = frame.parent()
        self.assertIsInstance(parent_of_frame, type(frame))

    def test_retrieve_children_of_part(self):
        bike = self.project.part('Bike')  # type:Part
        self.assertIsInstance(bike, Part)
        children_of_bike = bike.children()
        self.assertIsInstance(children_of_bike, PartSet)
        self.assertTrue(len(children_of_bike) >= 1)  # eg. Wheels ...

    def test_retrieve_siblings_of_part(self):
        """Test if the siblings of a part is the same as the children of the parent of the part"""
        frame = self.project.part('Frame')  # type:Part
        siblings_of_frame = frame.siblings()
        self.assertIsInstance(siblings_of_frame, PartSet)
        self.assertTrue(len(siblings_of_frame) >= 1)  # eg. Wheels ...

        # double check that the children of the parent of frame are the same as the siblings of frame
        children_of_parent_of_frame = frame.parent().children()  # type: PartSet
        self.assertEqual(len(children_of_parent_of_frame), len(siblings_of_frame))
        children_of_parent_of_frame_ids = [p.id for p in children_of_parent_of_frame]
        for sibling in siblings_of_frame:
            self.assertIn(sibling.id, children_of_parent_of_frame_ids,
                          'sibling {} is appearing in the siblings method and not in the children of ' \
                          'parent method'.format(sibling))

    def test_retrieve_part_without_parent_id(self):
        # only the root does not have a parent_id
        ROOT_NODE_ID = 'f521333e-a1ed-4e65-b166-999f91a38cf1'
        root_node = self.project.part(pk=ROOT_NODE_ID)  # type: Part
        self.assertTrue(hasattr(root_node, 'parent_id'))
        self.assertIsNone(root_node.parent_id)

    def test_retrieve_parent_of_part_without_parent_id(self):
        # only the root does not have a parent_id
        ROOT_NODE_ID = 'f521333e-a1ed-4e65-b166-999f91a38cf1'
        root_node = self.project.part(pk=ROOT_NODE_ID)  # type: Part
        parent_of_rootnode = root_node.parent()
        self.assertIsNone(parent_of_rootnode)

    def test_retrieve_siblings_of_part_without_parent_id(self):
        ROOT_NODE_ID = 'f521333e-a1ed-4e65-b166-999f91a38cf1'
        root_node = self.project.part(pk=ROOT_NODE_ID)  # type: Part
        siblings_of_root_node = root_node.siblings()
        self.assertIsInstance(siblings_of_root_node, PartSet)
        self.assertEqual(len(siblings_of_root_node), 0)

    # new in 1.3+
    def test_kwargs_on_part_retrieval(self):
        # test that the additional kwargs are added to the query filter on the api
        bikes = self.project.parts('Bike', descendants=True)  # type:PartSet
        self.assertTrue(len(bikes) == 1)
        self.assertTrue(self.client.last_url.find('descendants'))

    # new in 1.5+
    def test_edit_part_instance_name(self):
        front_fork = self.project.part('Front Fork')
        front_fork_oldname = str(front_fork.name)
        front_fork.edit(name='Front Fork - updated')

        front_fork_updated = self.project.part('Front Fork - updated')
        self.assertEqual(front_fork.id, front_fork_updated.id)
        self.assertEqual(front_fork.name, front_fork_updated.name)
        self.assertEqual(front_fork.name, 'Front Fork - updated')

        with self.assertRaises(IllegalArgumentError):
            front_fork.edit(name=True)

        # teardown
        front_fork.edit(name=front_fork_oldname)

    def test_edit_part_instance_description(self):
        front_fork = self.project.part('Front Fork')
        front_fork_olddescription = str(front_fork._json_data.get('description'))
        front_fork.edit(description='A normal Front Fork')

        front_fork_updated = self.project.part('Front Fork')
        self.assertEqual(front_fork.id, front_fork_updated.id)

        with self.assertRaises(IllegalArgumentError):
            front_fork.edit(description=42)

        # teardown
        front_fork.edit(description=front_fork_olddescription)

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
        pedal_model = self.project.model('Pedal')
        self.assertTrue(pedal.id, pedal_model.id)
        self.assertTrue(pedal._json_data['multiplicity'], 'ONE')

        # teardown
        pedal_model.delete()

    def test_add_proxy_to(self):
        catalog_container = self.project.model('Catalog container')
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
        catalog_model = self.project.model('Model')
        proxy_catalog_model = self.project.model('Proxy based on catalog model')
        retrieved_catalog_model = proxy_catalog_model.proxy_model()

        # Added to improve coverage. Assert whether NotFoundError is raised when proxy_model() method is applied to
        # a part that is not a proxy
        with self.assertRaises(NotFoundError):
            catalog_model.proxy_model()

        self.assertEqual(catalog_model.id, retrieved_catalog_model.id)

    def test_retrieve_proxy_of_instance(self):
        instance = self.project.part('Rear Wheel')

        with self.assertRaises(IllegalArgumentError):
            instance.proxy_model()

    # new in 1.8+
    def test_retrieve_part_multiplicity(self):
        bike_model = self.project.model('Bike')
        self.assertEqual(bike_model.multiplicity, Multiplicity.ONE)

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
        bike = self.project.part('Bike')  # type:Part
        self.assertIsInstance(bike, Part)
        children_of_bike = bike.children(name__icontains='Wheel')
        self.assertIsInstance(children_of_bike, PartSet)
        self.assertTrue(len(children_of_bike) >= 1)  # eg. Wheels ...

    def test_retrieve_siblings_of_part_with_additional_arguments(self):
        """Test if the siblings of a part is the same as the children of the parent of the part"""
        frame = self.project.part('Frame')  # type:Part
        siblings_of_frame = frame.siblings(name__icontains='Wheel')
        self.assertIsInstance(siblings_of_frame, PartSet)
        self.assertTrue(len(siblings_of_frame) >= 1)  # eg. Wheels ...


class TestPartUpdate(TestBetamax):
    # updated in 1.9
    def test_part_update_with_dictionary_without_name(self):
        # setup
        front_fork = self.project.part('Front Fork')  # type: Part
        saved_front_fork_properties = dict([(p.name, p.value) for p in front_fork.properties])

        # do tests
        update_dict = {
            'Material': 'Adamantium',
            'Height (mm)': 432.1,
            'Color': 'Earth Blue (new)'
        }
        front_fork.update(update_dict=update_dict)
        refreshed_front_fork = self.project.part(pk=front_fork.id)

        for prop in refreshed_front_fork.properties:
            self.assertIn(prop.name , update_dict, "property with {} should be in the update dict".format(prop.name))
            self.assertEqual(update_dict[prop.name] ,prop.value, "property {} with value {} did not match contents " \
                                                         "with KEC".format(prop.name, prop.value))

        # tearDown
        for prop_name, prop_value in saved_front_fork_properties.items():
            front_fork.property(prop_name).value = prop_value

    # new in 1.9
    def test_part_update_with_dictionary_including_name(self):
        # setup
        front_fork = self.project.part('Front Fork')  # type: Part
        saved_front_fork_properties = dict([(p.name, p.value) for p in front_fork.properties])

        # do tests
        update_dict = {
            'Material': 'Adamantium',
            'Height (mm)': 432.1,
            'Color': 'Earth Blue (new)'
        }
        front_fork.update(name='Better front fork', update_dict=update_dict)
        refreshed_front_fork = self.project.part(pk=front_fork.id)
        self.assertEqual(refreshed_front_fork.name, 'Better front fork')
        for prop in refreshed_front_fork.properties:
            self.assertIn(prop.name , update_dict, "property with {} should be in the update dict".format(prop.name))
            self.assertEqual(update_dict[prop.name] ,prop.value, "property {} with value {} did not match contents " \
                                                         "with KEC".format(prop.name, prop.value))

        with self.assertRaises(IllegalArgumentError):
            front_fork.update(name=12, update_dict=update_dict)

        # tearDown
        for prop_name, prop_value in saved_front_fork_properties.items():
            front_fork.property(prop_name).value = prop_value
        refreshed_front_fork.edit(name='Front Fork')

    def test_part_update_with_missing_property(self):
        # setup
        front_fork = self.project.part('Front Fork')  # type: Part
        saved_front_fork_properties = dict([(p.name, p.value) for p in front_fork.properties])

        # do tests
        update_dict = {
            'Unknown Property': 'Woot!'
        }
        with self.assertRaises(NotFoundError):
            front_fork.update(update_dict=update_dict)

        # tearDown
        for prop_name, prop_value in saved_front_fork_properties.items():
            front_fork.property(prop_name).value = prop_value

    # new in 1.15
    def test_part_update_with_property_ids(self):
        # setup
        front_fork = self.project.part('Front Fork')  # type: Part
        saved_front_fork_properties = dict([(p.name, p.value) for p in front_fork.properties])

        update_dict = dict()
        for p in front_fork.properties:
            if p.name == 'Color':
                update_dict[p.id] = 'Green'
            elif p.name == 'Material':
                update_dict[p.id] = 'Titanium'
            elif p.name == 'Height (mm)':
                update_dict[p.id] = '42'

        # do tests
        front_fork.update(update_dict=update_dict, use_ids=True)

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
        model_without_instances = self.project.model(name='model_without_instances')

        with self.assertRaises(NotFoundError):
            model_without_instances.instance()

    # new in 1.10
    def test_reorder_properties_using_names(self):
        # Retrieve the front fork model
        front_fork_model = self.project.model('Front Fork')

        # Sort the properties of the front fork model based on their original order
        original_sorted_list_of_props = sorted(front_fork_model.properties, key=lambda k: k._json_data['order'])

        # Make a new list with only the names of the properties sorted by order. This will later be used to
        # reverse the order to the initial status
        original_list_of_prop_names = [prop.name for prop in original_sorted_list_of_props]

        # Instantiate the list that will be used to reorder the properties
        desired_order_list = ['Material', 'Height (mm)', 'Color']

        # Make the call to re-order the properties according to the above list
        front_fork_model.order_properties(property_list=desired_order_list)

        # Re-retrieve the front fork model
        front_fork_model = self.project.model('Front Fork')

        # Do the same steps as above. This will be used to check whether the action performed correctly.
        new_sorted_list_of_props = sorted(front_fork_model.properties, key=lambda k: k._json_data['order'])
        new_list_of_prop_names = [prop.name for prop in new_sorted_list_of_props]

        # Check the new list with the desired one
        self.assertEqual(desired_order_list, new_list_of_prop_names)

        # Return the front fork model to the initial status
        front_fork_model.order_properties(property_list=original_list_of_prop_names)

    def test_reorder_properties_using_objects(self):
        # Retrieve the front fork model
        front_fork_model = self.project.model('Front Fork')

        # Sort the properties of the front fork model based on their original order
        original_sorted_list_of_props = sorted(front_fork_model.properties, key=lambda k: k._json_data['order'])

        # Instantiate the list that will be used to reorder the properties
        desired_order_list = [front_fork_model.property('Material'),
                              front_fork_model.property('Height (mm)'),
                              front_fork_model.property('Color')]

        # Make the call to re-order the properties according to the above list
        front_fork_model.order_properties(property_list=desired_order_list)

        # Re-retrieve the front fork model
        front_fork_model = self.project.model('Front Fork')

        # Create a list of property id's, after the properties have been sorted.
        # This will be used to check whether the action performed correctly.
        new_sorted_list_of_props = sorted(front_fork_model.properties, key=lambda k: k._json_data['order'])
        new_list_of_prop_ids = [prop.id for prop in new_sorted_list_of_props]

        # Create a list of property id's, based on the desired order.
        desired_order_list_ids = [prop.id for prop in desired_order_list]

        # Check the new list with the desired one
        self.assertEqual(desired_order_list_ids, new_list_of_prop_ids)

        # Return the front fork model to the initial status
        front_fork_model.order_properties(property_list=original_sorted_list_of_props)

    def test_reorder_wrong_properties(self):
        # Retrieve the front fork model
        front_fork_model = self.project.model('Front Fork')

        # Instantiate a wrong list that will be used to reorder the properties.
        desired_order_list = ['Material', 'Height (mm)', 'Color', 'Width (mm)']

        with self.assertRaises(NotFoundError):
            front_fork_model.order_properties(property_list=desired_order_list)

    def test_reorder_not_list(self):
        # Retrieve the front fork model
        front_fork_model = self.project.model('Front Fork')

        # Instantiate a wrong list that will be used to reorder the properties.
        desired_order_list = 'Material Height (mm) Color'

        with self.assertRaises(TypeError):
            front_fork_model.order_properties(property_list=desired_order_list)

    def test_reorder_properties_of_instance(self):
        # Retrieve the front fork model
        front_fork_instance = self.project.part(name='Front Fork', category='INSTANCE')

        # Instantiate a list that will be used to reorder the properties.
        desired_order_list = ['Material', 'Height (mm)', 'Color']

        with self.assertRaises(APIError):
            front_fork_instance.order_properties(property_list=desired_order_list)

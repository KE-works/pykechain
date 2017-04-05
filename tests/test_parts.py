from pykechain.exceptions import NotFoundError, MultipleFoundError, APIError
from pykechain.models import Part, PartSet
from tests.classes import TestBetamax


class TestParts(TestBetamax):
    def test_retrieve_parts(self):
        parts = self.project.parts()

        # Check if there are parts
        assert len(parts)

    def test_retrieve_single_part(self):
        part = self.project.part('One')

        assert part

    def test_retrieve_single_unknown(self):
        with self.assertRaises(NotFoundError):
            self.project.part('part-does-not-exist')

    def test_retrieve_single_multiple(self):
        with self.assertRaises(MultipleFoundError):
            self.project.part()

    def test_retrieve_models(self):
        many = self.project.model('Many')

        assert self.project.parts(model=many)

    def test_retrieve_model_unknown(self):
        with self.assertRaises(NotFoundError):
            self.client.model('model-does-not-exist')

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
        product = self.project.part('Product')
        many_model = self.project.model('Many')

        many_test = product.add(many_model, name='ManyTest')
        assert self.project.part('ManyTest')
        many_test.delete()

        many_test2 = many_model.add_to(product, name="ManyTest2")
        assert self.project.part('ManyTest2')
        many_test2.delete()

        with self.assertRaises(APIError):
            many_test2.delete()

    def test_part_html_table(self):
        part = self.project.part('One')

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
        one = self.project.part('One')  # type:Part
        parent = one.parent()
        assert type(parent) is Part

    def test_retrieve_children_of_part(self):
        product = self.project.part('Product')  # type:Part
        children = product.children()
        assert type(children) is PartSet
        assert len(children) >= 1

    def test_retrieve_siblings_of_part(self):
        """Test if the siblings of a part is the same as the children of the parent of the part"""
        one = self.project.part('One')  # type:Part
        siblings_of_one = one.siblings()
        assert type(siblings_of_one) is PartSet
        assert len(siblings_of_one) >= 1

        # double check that the children of the parent of frame are the same as the siblings of frame
        children_of_parent = one.parent().children()  # type: PartSet
        assert len(children_of_parent) == len(siblings_of_one)
        children_of_parent_ids = [p.id for p in children_of_parent]
        for sibling in siblings_of_one:
            assert sibling.id in children_of_parent_ids, \
                'sibling {} is appearing in the siblings method and not in the children of ' \
                'parent method'.format(sibling)

    def test_retrieve_part_without_parent_id(self):
        root_node = self.project.part('Product').parent()  # type: Part
        assert not root_node.parent_id

    def test_retrieve_parent_of_part_without_parent_id(self):
        root_node = self.project.part('Product').parent()  # type: Part
        parent_of_rootnode = root_node.parent()
        assert parent_of_rootnode is None

    def test_retrieve_siblings_of_part_without_parent_id(self):
        root_node = self.project.part('Product').parent()  # type: Part
        siblings_of_root_node = root_node.siblings()
        assert type(siblings_of_root_node) is PartSet
        assert len(siblings_of_root_node) is 0

    # new in 1.3+
    def test_kwargs_on_part_retrieval(self):
        # test that the additional kwargs are added to the query filter on the api
        parts = self.project.parts('Product', descendants=True)  # type:Part
        assert len(parts) > 1
        assert self.client.last_url.find('descendants')

    # new in 1.5+
    def test_edit_part_instance_name(self):
        one = self.project.part('One')
        one.edit(name='One2')

        one_u = self.project.part(pk=one.id)
        assert one_u.name == "One2"

        one_u.edit(name='One')

    def test_edit_part_instance_description(self):
        one = self.project.part('One')
        one.edit(description='Test Description')

        one_u = self.project.part(pk=one.id)
        assert one_u._json_data['description'] == 'Test Description'

        one_u.edit(description='')

    def test_edit_part_model_name(self):
        one = self.project.model('One')
        one.edit(name='One2')

        one_u = self.project.model(pk=one.id)
        assert one_u.name == 'One2'

        one_u.edit(name='One')


class TestPartUpdate(TestBetamax):
    def test_part_update_with_dictionary(self):
        # setup
        one = self.project.part('One')  # type: Part
        saved_properties = dict([(p.name, p.value) for p in one.properties])

        update_dict = {
            'Float': 12.4,
            'Integer': 1,
            'String': 'hey'
        }

        one.update(update_dict)
        refreshed = self.project.part(pk=one.id)

        for prop, value in update_dict.items():
            assert refreshed.property(prop).value == value

        # tearDown
        for prop in update_dict:
            refreshed.property(prop).value = saved_properties[prop]

    def test_part_update_with_missing_property(self):
        # setup
        one = self.project.part('One')  # type: Part

        with self.assertRaises(NotFoundError):
            one.update({
                'property-does-not-exist': None
            })


class TestPartCreateWithProperties(TestBetamax):
    def test_create_part_with_properties_no_bulk(self):
        """Test create a part with the properties when bulk = False for old API compatibility"""
        parent = self.project.part('Product')  # type: Part
        many_model = self.project.model('Many')  #type: Part

        update_dict = {
            'Float': 42.42,
            'Integer': 42,
        }

        new = parent.add_with_properties(many_model, "ManyX", update_dict=update_dict, bulk=False)

        self.assertEqual(type(new), Part)
        self.assertTrue(new.property('Float'), 42.42)

        new.delete()

    def test_create_part_with_properties_with_bulk(self):
        """Test create a part with the properties with bulk"""
        parent = self.project.part('Product')  # type: Part
        many_model = self.project.model('Many')  #type: Part

        update_dict = {
            'Float': 42.42,
            'Integer': 42,
        }

        new = parent.add_with_properties(many_model, "ManyX", update_dict=update_dict, bulk=True)

        self.assertEqual(type(new), Part)
        self.assertTrue(new.property('Float'), 42.42)

        new.delete()



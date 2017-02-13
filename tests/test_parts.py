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
        children_of_parent_of_frame = frame.parent().children() # type: PartSet
        assert len(children_of_parent_of_frame) == len(siblings_of_frame)
        children_of_parent_of_frame_ids = [p.id for p in children_of_parent_of_frame]
        for sibling in siblings_of_frame:
            assert sibling.id in children_of_parent_of_frame_ids, \
                'sibling {} is appearing in the siblings method and not in the children of ' \
                'parent method'.format(sibling)

    def test_retrieve_part_without_parent_id(self):
        # only the root does not have a parent_id
        ROOT_NODE_ID = 'f521333e-a1ed-4e65-b166-999f91a38cf1'
        root_node = self.project.part(pk=ROOT_NODE_ID)  #type: Part
        assert hasattr(root_node, 'parent_id')
        assert root_node.parent_id == None

    def test_retrieve_parent_of_part_without_parent_id(self):
        # only the root does not have a parent_id
        ROOT_NODE_ID = 'f521333e-a1ed-4e65-b166-999f91a38cf1'
        root_node = self.project.part(pk=ROOT_NODE_ID)  #type: Part
        parent_of_rootnode = root_node.parent()
        assert parent_of_rootnode is None

    def test_retrieve_siblings_of_part_without_parent_id(self):
        ROOT_NODE_ID = 'f521333e-a1ed-4e65-b166-999f91a38cf1'
        root_node = self.project.part(pk=ROOT_NODE_ID)  #type: Part
        siblings_of_root_node = root_node.siblings()
        assert type(siblings_of_root_node) is PartSet
        assert len(siblings_of_root_node) is 0

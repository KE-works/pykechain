from pykechain.exceptions import NotFoundError, MultipleFoundError, APIError
from tests.classes import TestBetamax


class TestParts(TestBetamax):

    def test_retrieve_parts(self):
        parts = self.client.parts()

        # Check if there are parts
        assert len(parts)

    def test_retrieve_single_part(self):
        part = self.client.part('Unique Wheel')

        assert part

    def test_retrieve_single_unknown(self):
        with self.assertRaises(NotFoundError):
            self.client.part('123lladadwd')

    def test_retrieve_single_multiple(self):
        with self.assertRaises(MultipleFoundError):
            self.client.part('Frame')

    def test_retrieve_models(self):
        project = self.client.scope('Bike Project')
        wheel = project.model('Wheel')

        assert project.parts(model=wheel)

    def test_retrieve_model_unknown(self):
        with self.assertRaises(NotFoundError):
            self.client.model('123lladadwd')

    def test_retrieve_model_multiple(self):
        with self.assertRaises(MultipleFoundError):
            self.client.model('Frame')

    def test_part_set_iterator(self):
        for part in self.client.parts():
            assert part.name

    def test_part_set_get_item_invalid(self):
        part_set = self.client.parts()

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
        part = self.client.part('Unique Wheel')

        assert "</table>" in part._repr_html_()

    def test_part_set_html_table(self):
        parts = self.client.parts()

        assert "</table>" in parts._repr_html_()

    def test_part_set_html_categories(self):
        parts = self.client.parts(category=None)

        assert "<th>Category</th>" in parts._repr_html_()

from pykechain.exceptions import NotFoundError, MultipleFoundError
from tests.betamax import TestBetamax


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

    def test_part_set_iterator(self):
        for part in self.client.parts():
            assert part.name

    def test_part_add_delete_part(self):
        project = self.client.scope('Bike Project')

        bike = project.part('Bike')
        wheel = project.model('Wheel')

        wheel = bike.add(wheel, name='Test Wheel')

        wheel.delete()

    def test_part_html_table(self):
        part = self.client.part('Unique Wheel')

        assert "</table>" in part._repr_html_()

    def test_part_set_html_table(self):
        parts = self.client.parts()

        assert "</table>" in parts._repr_html_()

    def test_part_set_html_categories(self):
        parts = self.client.parts(category=None)

        assert "<th>Category</th>" in parts._repr_html_()

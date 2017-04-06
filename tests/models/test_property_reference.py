from tests.classes import TestBetamax


class TestReferenceProperty(TestBetamax):

    def setUp(self):
        super(TestReferenceProperty, self).setUp()

        self.ref = self.project.part('One').property('Reference')

    def test_set_invalid_reference_value(self):

        with self.assertRaises(ValueError):
            self.ref.value = 0

        with self.assertRaises(ValueError):
            self.ref.value = False

        with self.assertRaises(ValueError):
            self.ref.value = [1, 2, 3]

    def test_set_reference_to_part(self):
        wheel = self.project.part('Many1')

        self.ref.value = wheel

        assert self.ref.value.name == 'Many1'

        self.ref.value = None

    def test_set_reference_to_part_id(self):
        wheel = self.project.part('Many2')

        self.ref.value = wheel.id

        assert self.ref.value.name == 'Many2'

        self.ref.value = None

    def test_delete_reference(self):
        self.ref.value = None

        assert self.ref.value is None

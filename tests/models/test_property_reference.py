from tests.classes import TestBetamax


class TestReferenceProperty(TestBetamax):
    def setUp(self):
        super(TestReferenceProperty, self).setUp()

        self.ref = self.project.part('Bike').property('RefTest')

    def test_set_invalid_reference_value(self):
        with self.assertRaises(ValueError):
            self.ref.value = 0

        with self.assertRaises(ValueError):
            self.ref.value = False

        with self.assertRaises(ValueError):
            self.ref.value = [1, 2, 3]

    def test_set_reference_to_part(self):
        wheel = self.project.part('Front Wheel')

        self.ref.value = wheel

        self.assertEqual(self.ref.value.name, 'Front Wheel')

    def test_set_reference_to_part_id(self):
        wheel = self.project.part('Front Wheel')

        self.ref.value = wheel.id

        self.assertEqual(self.ref.value.name, 'Front Wheel')

    def test_delete_reference(self):
        self.ref.value = None

        self.assertIsNone(self.ref.value)

    def test_retrieve_parts(self):
        reference_property_parts = self.ref.choices()
        wheel_model = self.project.model('Wheel')
        instances_of_wheel_model = self.project.parts(model=wheel_model)
        self.assertEqual(len(reference_property_parts), len(instances_of_wheel_model))
        self.assertEqual(instances_of_wheel_model._parts[0].id, reference_property_parts[0].id)
        self.assertEqual(instances_of_wheel_model._parts[1].id, reference_property_parts[1].id)


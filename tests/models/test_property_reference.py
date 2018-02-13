from tests.classes import TestBetamax


class TestMultiReferenceProperty(TestBetamax):
    def setUp(self):
        super(TestMultiReferenceProperty, self).setUp()

        self.mref_prop = self.project.part('Bike').property('RefTest') # type: MultiReferenceProperty

    def test_set_invalid_reference_value(self):
        with self.assertRaises(ValueError):
            self.mref_prop.value = 0

        with self.assertRaises(ValueError):
            self.mref_prop.value = False

        with self.assertRaises(ValueError):
            self.mref_prop.value = [1, 2, 3]

    def test_set_reference_to_part(self):
        wheel = self.project.part('Front Wheel')

        self.mref_prop.value = [wheel]
        self.assertEqual(self.mref_prop.value[0].name, 'Front Wheel')

    def test_set_reference_to_part_id(self):
        wheel = self.project.part('Front Wheel')

        self.mref_prop.value = [wheel.id]

        self.assertEqual(self.mref_prop.value[0].name, 'Front Wheel')

    def test_delete_reference(self):
        self.mref_prop.value = None

        self.assertIsNone(self.mref_prop.value)

    def test_retrieve_parts(self):
        reference_property_parts = self.mref_prop.choices()
        wheel_model = self.project.model('Wheel')
        instances_of_wheel_model = self.project.parts(model=wheel_model)
        self.assertEqual(len(reference_property_parts), len(instances_of_wheel_model))
        self.assertEqual(instances_of_wheel_model._parts[0].id, reference_property_parts[0].id)
        self.assertEqual(instances_of_wheel_model._parts[1].id, reference_property_parts[1].id)

    def test_value_if_multi_ref_gives_back_all_parts(self):
        """because of #276 problem"""
        model_instance = self.project.part('Instance of Model')
        multi_ref_prop = model_instance.property(name='part reference field')

        all_referred_parts = multi_ref_prop.value
        self.assertEqual(len(all_referred_parts), len(multi_ref_prop._value))



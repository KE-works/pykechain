from tests.classes import TestBetamax
from unittest import skip


class TestReferenceProperty(TestBetamax):
    @skip('KE-chain deprecated property type')
    def setUp(self):
        super(TestReferenceProperty, self).setUp()

        self.ref = self.project.part('Bike').property('Test reference property')

    @skip('KE-chain deprecated property type')
    def test_set_invalid_reference_value(self):
        with self.assertRaises(ValueError):
            self.ref.value = 0

        with self.assertRaises(ValueError):
            self.ref.value = False

        with self.assertRaises(ValueError):
            self.ref.value = [1, 2, 3]

    @skip('KE-chain deprecated property type')
    def test_set_reference_to_part(self):
        wheel = self.project.part('Front Wheel')

        self.ref.value = [wheel]

        self.assertEqual(self.ref[0].value.name, 'Front Wheel')

    @skip('KE-chain deprecated property type')
    def test_set_reference_to_part_id(self):
        wheel = self.project.part('Front Wheel')

        self.ref.value = [wheel.id]

        self.assertEqual(self.ref.value[0].name, 'Front Wheel')

    @skip('KE-chain deprecated property type')
    def test_delete_reference(self):
        self.ref.value = None

        self.assertIsNone(self.ref.value)

    @skip('KE-chain deprecated property type')
    def test_retrieve_parts(self):
        reference_property_parts = self.ref.choices()
        wheel_model = self.project.model('Wheel')
        instances_of_wheel_model = self.project.parts(model=wheel_model)
        self.assertEqual(len(reference_property_parts), len(instances_of_wheel_model))
        self.assertEqual(instances_of_wheel_model._parts[0].id, reference_property_parts[0].id)
        self.assertEqual(instances_of_wheel_model._parts[1].id, reference_property_parts[1].id)


class TestMultiReferenceProperty(TestBetamax):
    def setUp(self):
        super(TestMultiReferenceProperty, self).setUp()

        self.ref = self.project.part('Bike').property('Test multi reference property')
        self.ref_model = self.project.model('Bike').property('Test multi reference property')

    def test_referencing_a_model(self):
        # setUp
        wheel_model = self.project.model('Wheel')
        self.ref_model.value = [wheel_model]

        # testing
        self.assertEqual(len(self.ref_model.value), 1)

    def test_referencing_multiple_instances_using_parts(self):
        # setUp
        wheel_model = self.project.model('Wheel')
        wheel_instances = wheel_model.instances()
        wheel_instances_list = [instance for instance in wheel_instances]
        self.ref.value = wheel_instances_list

        # testing
        self.assertEqual(len(self.ref.value), 2)

        # tearDown
        self.ref.value = None

    def test_referencing_multiple_instances_using_ids(self):
        # setUp
        wheel_model = self.project.model('Wheel')
        wheel_instances = wheel_model.instances()
        wheel_instances_list = [instance.id for instance in wheel_instances]
        self.ref.value = wheel_instances_list

        # testing
        self.assertEqual(len(self.ref.value), 2)

        # tearDown
        self.ref.value = None

    def test_referencing_a_part_not_in_a_list(self):
        # setUp
        front_wheel = self.project.part('Front Wheel')

        # testing
        with self.assertRaises(ValueError):
            self.ref.value = front_wheel

    def test_referencing_a_list_with_no_parts(self):
        # setUp
        fake_part = [15, 21, 26]

        # testing
        with self.assertRaises(ValueError):
            self.ref.value = fake_part

    def test_value_if_multi_ref_gives_back_all_parts(self):
        """because of #276 problem"""
        # setUp
        wheel_model = self.project.model('Wheel')
        wheel_instances = wheel_model.instances()
        wheel_instances_list = [instance.id for instance in wheel_instances]
        self.ref.value = wheel_instances_list

        # testing
        all_referred_parts = self.ref.value
        self.assertEqual(len(all_referred_parts), len(self.ref._value))

        # tearDown
        self.ref.value = None

    def test_value_if_nothing_is_referenced(self):
        # setUp
        value_of_multi_ref = self.ref.value

        # testing
        self.assertEqual(None, value_of_multi_ref)

    def test_multi_ref_choices(self):
        # testing
        possible_options = self.ref.choices()
        self.assertEqual(2, len(possible_options))


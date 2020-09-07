from pykechain.enums import PropertyType, Multiplicity
from pykechain.exceptions import IllegalArgumentError
from pykechain.models import Part
from pykechain.models.validators import RequiredFieldValidator
from pykechain.utils import is_uuid
from tests.classes import TestBetamax


class TestPartCreateWithProperties(TestBetamax):

    def setUp(self):
        super().setUp()
        self.parent = self.project.part('Bike')  # type: Part
        self.wheel_model = self.project.model('Wheel')  # type: Part
        self.new_wheel = None

    def tearDown(self):
        if self.new_wheel:
            self.new_wheel.delete()
        super().tearDown()

    def test_create_part_with_properties_no_bulk(self):
        """Test create a part with the properties when bulk = False for old API compatibility"""
        update_dict = {
            'Diameter': 42.42,
            'Spokes': 42,
            'Rim Material': 'Unobtanium'
        }

        self.new_wheel = self.parent.add_with_properties(
            self.wheel_model,
            "Fresh Wheel",
            update_dict=update_dict,
            bulk=False,
        )

        self.assertIsInstance(self.new_wheel, Part)
        self.assertTrue(self.new_wheel.property('Diameter'), 42.42)

    def test_create_part_with_properties_names_with_bulk(self):
        """Test create a part with the properties when bulk = False for old API compatibility"""
        update_dict = {
            'Diameter': 42.43,
            'Spokes': 42,
            'Rim Material': 'Unobtanium'
        }

        self.new_wheel = self.parent.add_with_properties(
            self.wheel_model,
            "Fresh Wheel",
            update_dict=update_dict,
            bulk=True,
        )

        self.assertIsInstance(self.new_wheel, Part)
        self.assertTrue(self.new_wheel.property('Diameter'), 42.43)

    def test_create_part_with_properties_ids_with_bulk(self):
        """Test create a part with the properties when bulk = False for old API compatibility"""
        update_dict = {
            self.wheel_model.property('Diameter').id: 42.43,
            self.wheel_model.property('Spokes').id: 42,
            self.wheel_model.property('Rim Material').id: 'Unobtanium'
        }

        # check if the keys are really a UUID
        self.assertTrue(any([is_uuid(key) for key in update_dict.keys()]))

        self.new_wheel = self.parent.add_with_properties(
            self.wheel_model,
            "Fresh Wheel",
            update_dict=update_dict,
            bulk=True,
        )

        self.assertIsInstance(self.new_wheel, Part)
        self.assertTrue(self.new_wheel.property('Diameter'), 42.43)


class TestCreateModelWithProperties(TestBetamax):
    properties_fvalues = [
        {"name": "char prop", "property_type": PropertyType.CHAR_VALUE},
        {"name": "number prop", "property_type": PropertyType.FLOAT_VALUE, "value": 3.14},
        {"name": "boolean_prop", "property_type": PropertyType.BOOLEAN_VALUE, "value": False,
         "value_options": {"validators": [RequiredFieldValidator().as_json()]}}
    ]

    def setUp(self):
        super().setUp()
        self.new_part = None

    def tearDown(self):
        if self.new_part is not None:
            self.new_part.delete()
        super().tearDown()

    def test_create_model_with_properties(self):
        parent = self.project.model(name__startswith='Catalog')

        new_model = self.project.create_model_with_properties(
            name='A new model',
            parent=parent.id,
            multiplicity=Multiplicity.ZERO_MANY,
            properties_fvalues=self.properties_fvalues,
        )
        self.new_part = new_model

        self.assertEqual(3, len(new_model.properties))
        self.assertEqual(new_model.property('number prop').value, 3.14)
        self.assertEqual(new_model.property('boolean_prop').value, False)
        self.assertTrue(new_model.property('boolean_prop')._options)

    def test_create_with_invalid_properties(self):
        parent = self.project.model(name__startswith='Catalog')

        with self.assertRaises(IllegalArgumentError):
            self.new_part = self.project.create_model_with_properties(
                name='A new model',
                parent=parent.id,
                multiplicity=Multiplicity.ZERO_MANY,
                properties_fvalues=[
                    {"property_type": PropertyType.CHAR_VALUE}
                ],
            )

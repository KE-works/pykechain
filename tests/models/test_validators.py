from jsonschema import validate, ValidationError

from pykechain.enums import PropertyVTypes
from pykechain.models import Property
from pykechain.models.validators import PropertyValidator, ValidatorEffect, VisualEffect, ValidVisualEffect, \
    InvalidVisualEffect, NumericRangeValidator, BooleanFieldValidator
from pykechain.models.validators.validator_schemas import options_json_schema, validator_jsonschema_stub, \
    effects_jsonschema_stub
from pykechain.models.validators.validators import RegexStringValidator
from tests.classes import SixTestCase


class TestValidatorJSON(SixTestCase):
    def test_valid_numeric_range_validator_json(self):
        options = dict(
            validators=[dict(
                vtype='numericRangeValidator',
                config=dict(
                    minvalue=2,
                    maxvalue=10,
                    stepsize=2,
                    on_valid=[dict(effect="CssEffect", config=dict(applyCss="valid"))],
                    on_invalid=[dict(effect="CssEffect", config=dict(applyCss="invalid")),
                                dict(effect="ErrorText",
                                     config=dict(text="Range should be between 2 and 10 with step 2."))]
                )
            )]
        )

        validate(options_json_schema, options)

    def test_valid_requiredfield_validator_json(self):
        options = {'validators': [
            {
                'vtype': 'requiredFieldValidator',
                'config': {
                    'effects_when_valid': [],
                    'effects_when_invalid': [{'effect': "ErrorText", 'config': {'Text': "This field is required."}}]
                }
            }, {
                'vtype': 'numericRangeValidator',
                'config': {'minValue': 0}
            }
        ]}

        validate(options_json_schema, options)

    def test_valid_booleanfield_validator_json(self):
        options = {'validators': [{
            'vtype': 'booleanFieldValidator',
            'config': {
                'is_valid': False,
                'is_invalid': [True, None],
                'effects_when_valid': [],
                'effects_when_invalid': [{'effect': 'ErrorText', 'text': 'Value of the field should be False'}]}
        }]}

        validate(options_json_schema, options)

    def test_validator_invalid_vtype(self):
        validator_json = {
            'vtype': 'invalid',
            'config': {}
        }
        with self.assertRaisesRegex(ValidationError, "'invalid' is not one of"):
            validate(validator_json, validator_jsonschema_stub)

    def test_validator_missing_vtype(self):
        validator_json = {
            'config': {}
        }
        with self.assertRaisesRegex(ValidationError, "'vtype' is a required property"):
            validate(validator_json, validator_jsonschema_stub)

    def test_validator_config_not_a_dict(self):
        v = {
            'vtype': PropertyVTypes.NUMERICRANGE,
            'config': []
        }
        with self.assertRaisesRegex(ValidationError, "is not of type 'object'"):
            validate(v, validator_jsonschema_stub)

    def test_validator_on_valid_not_a_list(self):
        v = {
            'vtype': PropertyVTypes.NUMERICRANGE,
            'config': {
                'on_valid': {}
            }
        }
        with self.assertRaisesRegex(ValidationError, "is not of type 'array'"):
            validate(v, validator_jsonschema_stub)

    def test_validator_on_invalid_not_a_list(self):
        v = {
            'vtype': PropertyVTypes.NUMERICRANGE,
            'config': {
                'on_invalid': {}
            }
        }
        with self.assertRaisesRegex(ValidationError, "is not of type 'array'"):
            validate(v, validator_jsonschema_stub)

    def test_validator_on_valid_list_with_obj(self):
        v = {
            'vtype': PropertyVTypes.NUMERICRANGE,
            'config': {
                'on_valid': [{'effect': '', 'config': {}}]
            }
        }
        validate(v, validator_jsonschema_stub)

    def test_validator_on_invalid_list_with_obj(self):
        v = {
            'vtype': PropertyVTypes.NUMERICRANGE,
            'config': {
                'on_invalid': [{'effect': '', 'config': {}}]
            }
        }
        validate(v, validator_jsonschema_stub)

    def test_validatoreffect_requires_effect_property(self):
        v = {}
        with self.assertRaisesRegex(ValidationError, "'effect' is a required property"):
            validate(v, effects_jsonschema_stub)

    def test_validatoreffect_requires_config_property(self):
        v = {'effect': ''}
        with self.assertRaisesRegex(ValidationError, "'config' is a required property"):
            validate(v, effects_jsonschema_stub)

    def test_validatoreffect_not_allows_additional_properties(self):
        v = {
            'effect': '',
            'config': {},
            'additional_option': None

        }
        with self.assertRaisesRegex(ValidationError,
                                    r"Additional properties are not allowed \('additional_option' was unexpected\)"):
            validate(v, effects_jsonschema_stub)


class TestPropertyValidatorClass(SixTestCase):
    def test_propertyvalidator_produces_valid_json(self):
        pv = PropertyValidator()
        pv.validate_json()


class TestValidatorEffects(SixTestCase):
    def test_validator_effect_produces_valid_json(self):
        ve = ValidatorEffect()
        ve.validate_json()

    def test_visual_effect_produces_valid_json(self):
        ve = VisualEffect()
        self.assertTrue('applyCss' in ve.as_json().get('config'))
        ve.validate_json()

    def test_valid_visualeffect_produces_valid_json(self):
        ve = ValidVisualEffect()
        self.assertTrue('applyCss' in ve.as_json().get('config'))
        ve.validate_json()

    def test_invalid_visualeffect_productes_valid_json(self):
        ve = InvalidVisualEffect()
        self.assertTrue('applyCss' in ve.as_json().get('config'))
        ve.validate_json()


class TestValidatorParsing(SixTestCase):

    def test_valid_numeric_range_validator_json(self):
        validator_json = dict(
            vtype='numericRangeValidator',
            config=dict(
                minvalue=2,
                maxvalue=10,
                stepsize=2,
                enforce_stepsize=False,
                on_valid=[dict(effect="visualEffect", config=dict(applyCss="valid"))],
                on_invalid=[dict(effect="visualEffect", config=dict(applyCss="invalid")),
                            dict(effect="errorTextEffect",
                                 config=dict(text="Range should be between 2 and 10 with step 2."))]
            )
        )

        validator = PropertyValidator.parse(validator_json)

        self.assertIsInstance(validator, NumericRangeValidator)
        self.assertTrue(validator.validate_json)
        pass


class TestValidatorDumping(SixTestCase):

    def test_valid_numeric_range_validator_dumped(self):
        validator_json = dict(
            vtype='numericRangeValidator',
            config=dict(
                minvalue=2,
                maxvalue=10,
                stepsize=2,
                enforce_stepsize=False,
                on_valid=[dict(effect="visualEffect", config=dict(applyCss="valid"))],
                on_invalid=[dict(effect="visualEffect", config=dict(applyCss="invalid")),
                            dict(effect="errorTextEffect",
                                 config=dict(text="Range should be between 2 and 10 with step 2."))]
            )
        )

        validator = PropertyValidator.parse(validator_json)
        self.assertIsInstance(validator, NumericRangeValidator)

        dumped_json = validator.as_json()
        self.assertIsNone(validate(dumped_json, validator_jsonschema_stub))
        self.assertIsNone(validator.validate_json())


class TestNumericRangeValidator(SixTestCase):
    def test_numeric_range_without_settings_validated_json(self):
        validator = NumericRangeValidator()

        as_json = validator.as_json()
        self.assertIsNone(validator.validate_json())
        self.assertIsInstance(as_json, dict)
        self.assertDictEqual(as_json, {'config': {}, 'vtype': 'numericRangeValidator'})

    def test_numeric_range_validates_with_lower_bound(self):
        validator = NumericRangeValidator(minvalue=0)
        self.assertTrue(validator.is_valid(1))

    def test_numeric_range_validates_with_max_bound(self):
        validator = NumericRangeValidator(maxvalue=10)
        self.assertTrue(validator.is_valid(1))

    def test_numeric_range_validates_with_min_max_bound(self):
        validator = NumericRangeValidator(maxvalue=10, minvalue=0)
        self.assertTrue(validator.is_valid(1))

    def test_numeric_range_invalidates_with_lower_bound(self):
        validator = NumericRangeValidator(minvalue=0)
        self.assertFalse(validator.is_valid(-1))

    def test_numeric_range_invalidates_with_max_bound(self):
        validator = NumericRangeValidator(maxvalue=0)
        self.assertFalse(validator.is_valid(1))

    def test_numeric_range_invalidates_with_min_max_bound(self):
        validator = NumericRangeValidator(maxvalue=10, minvalue=0)
        self.assertFalse(validator.is_valid(-1))

    def test_numeric_range_validates_with_min_max_bound_float(self):
        validator = NumericRangeValidator(maxvalue=10., minvalue=0.)
        self.assertTrue(validator.is_valid(1.5))

    def test_numeric_range_validates_with_stepsize_float(self):
        validator = NumericRangeValidator(stepsize=0.2, enforce_stepsize=True)
        self.assertTrue(validator.is_valid(1.2))
        self.assertTrue(validator.is_invalid(1.3))

    def test_numeric_range_validates_with_stepsize_int_with_minvalue(self):
        validator = NumericRangeValidator(minvalue=11, stepsize=2, enforce_stepsize=True)
        self.assertTrue(validator.is_valid(13))
        self.assertTrue(validator.is_invalid(16))


class TestBooleanFieldValidator(SixTestCase):
    def test_boolean_validator_without_settings(self):
        validator = BooleanFieldValidator()
        self.assertIsNone(validator.validate_json())
        self.assertIsInstance(validator.as_json(), dict)
        self.assertDictEqual(validator.as_json(), {'config': {}, 'vtype': 'booleanFieldValidator'})


class TestRegexValidator(SixTestCase):
    def test_regex_validator_without_settings(self):
        validator = RegexStringValidator()
        self.assertIsNone(validator.validate_json())
        self.assertIsInstance(validator.as_json(), dict)
        self.assertDictEqual(validator.as_json(), {'config': {}, 'vtype': 'regexStringValidator'})

    def test_regex_validator_with_pattern_match(self):
        validator = RegexStringValidator(pattern=r'.*')

        self.assertTrue(validator('mr cactus is tevree'))


class TestPropertyWithValidator(SixTestCase):

    def test_property_without_validator(self):
        prop = Property(json={}, client=None)
        self.assertIsNone(prop.is_valid)
        self.assertIsNone(prop.is_invalid)
        self.assertIsNone(prop.validate())

    def test_property_with_numeric_range_validator(self):
        prop_json = dict(
            value=1,
            options=dict(
                validators=[NumericRangeValidator(minvalue=0, maxvalue=10).as_json()]
            ))
        prop = Property(json=prop_json, client=None)
        self.assertTrue(prop.is_valid)
        self.assertFalse(prop.is_invalid)
        self.assertTrue(prop.validate())

    def test_property_with_numeric_range_validator_value_is_none(self):
        prop_json = dict(
            value=None,
            options=dict(
                validators=[NumericRangeValidator(minvalue=0, maxvalue=10).as_json()]
            ))
        prop = Property(json=prop_json, client=None)
        self.assertIsNone(prop.is_valid)
        self.assertIsNone(prop.is_invalid)
        self.assertListEqual(prop.validate(), [(None, None)])

    def test_property_with_boolean_validator(self):
        pass

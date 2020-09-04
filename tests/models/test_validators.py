from jsonschema import validate, ValidationError

from pykechain.enums import PropertyVTypes, PropertyType
from pykechain.exceptions import IllegalArgumentError
from pykechain.models import Property, AttachmentProperty
from pykechain.models.validators import PropertyValidator, ValidatorEffect, VisualEffect, ValidVisualEffect, \
    InvalidVisualEffect, NumericRangeValidator, BooleanFieldValidator
from pykechain.models.validators.validator_schemas import options_json_schema, validator_jsonschema_stub, \
    effects_jsonschema_stub
from pykechain.models.validators.validators import RegexStringValidator, RequiredFieldValidator, EvenNumberValidator, \
    OddNumberValidator, SingleReferenceValidator, EmailValidator, AlwaysAllowValidator, FileSizeValidator, \
    FileExtensionValidator
from tests.classes import SixTestCase, TestBetamax


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
        validator = NumericRangeValidator(minvalue=5)
        self.assertTrue(validator.is_valid(6))

    def test_numeric_range_validates_with_max_bound(self):
        validator = NumericRangeValidator(maxvalue=0)
        self.assertTrue(validator.is_valid(-3))
        validator = NumericRangeValidator(maxvalue=10)
        self.assertTrue(validator.is_valid(1))

    def test_numeric_range_validates_with_min_max_bound(self):
        validator = NumericRangeValidator(maxvalue=10, minvalue=0)
        self.assertTrue(validator.is_valid(1))

    def test_numeric_range_invalidates_with_lower_bound(self):
        validator = NumericRangeValidator(minvalue=0)
        self.assertFalse(validator.is_valid(-1))
        validator = NumericRangeValidator(minvalue=5)
        self.assertFalse(validator.is_valid(2))

    def test_numeric_range_invalidates_with_max_bound(self):
        validator = NumericRangeValidator(maxvalue=0)
        self.assertFalse(validator.is_valid(1))
        validator = NumericRangeValidator(maxvalue=5)
        self.assertFalse(validator.is_valid(6))

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

    def test_numeric_range_raises_exception_when_min_is_greater_than_max(self):
        with self.assertRaisesRegex(Exception, 'should be smaller than the maxvalue'):
            NumericRangeValidator(minvalue=11, maxvalue=-11)

    def test_numeric_range_raises_exception_when_enforce_stepsize_without_stepsize(self):
        with self.assertRaisesRegex(Exception, 'The stepsize should be provided when enforcing stepsize'):
            NumericRangeValidator(stepsize=None, enforce_stepsize=True)

    def test_numeric_range_does_not_respect_max_issue_435(self):
        """With reference to issue #435

        In KE-chain I've added a property with numeric range validators min = unbound and max = 1000.
        A value of 3333 simply returns as valid in pykechain:
        _validation_reasons =>'Value \'3333\' is between -inf and inf'
        """
        validator = NumericRangeValidator(maxvalue=1000)
        self.assertFalse(validator.is_valid(3333))
        self.assertRegex(validator.get_reason(), "Value '3333' should be between -inf and 1000")


class TestBooleanFieldValidator(SixTestCase):
    def test_boolean_validator_without_settings(self):
        validator = BooleanFieldValidator()
        self.assertIsNone(validator.validate_json())
        self.assertIsInstance(validator.as_json(), dict)
        self.assertDictEqual(validator.as_json(), {'config': {}, 'vtype': 'booleanFieldValidator'})


class TestRequiredFieldValidator(SixTestCase):
    def test_requiredfield_validator_without_settings(self):
        validator = RequiredFieldValidator()
        self.assertIsNone(validator.validate_json())
        self.assertIsInstance(validator.as_json(), dict)
        self.assertDictEqual(validator.as_json(), {'config': {}, 'vtype': 'requiredFieldValidator'})

    def test_requiredfield_validator_is_false_on_nonevalue(self):
        validator = RequiredFieldValidator()
        self.assertFalse(validator.is_valid(None))
        self.assertFalse(validator.is_valid(''))
        self.assertFalse(validator.is_valid([]))
        self.assertFalse(validator.is_valid(list()))
        self.assertFalse(validator.is_valid(tuple()))
        self.assertFalse(validator.is_valid(set()))

        # the value 'False' is not a None value so that is True (placed in other test)
        # self.assertFalse(validator.is_valid(False))

    def test_requiredfield_validator_is_true_on_value(self):
        validator = RequiredFieldValidator()
        self.assertTrue(validator.is_valid(1))
        self.assertTrue(validator.is_valid(0))
        self.assertTrue(validator.is_valid(0.0))
        self.assertTrue(validator.is_valid(float('inf')))
        self.assertTrue(validator.is_valid('string'))
        self.assertTrue(validator.is_valid({'key': 'val'}))
        self.assertTrue(validator.is_valid([1, 2, 3]))
        self.assertTrue(validator.is_valid((1,)))
        self.assertTrue(validator.is_valid({1, 2, 3}))
        self.assertTrue(validator.is_valid(False))


class TestRegexValidator(SixTestCase):
    def test_regex_validator_without_settings(self):
        validator = RegexStringValidator()
        self.assertIsNone(validator.validate_json())
        self.assertIsInstance(validator.as_json(), dict)
        self.assertDictEqual(validator.as_json(), {'config': {}, 'vtype': 'regexStringValidator'})

    def test_regex_validator_with_pattern_match(self):
        validator = RegexStringValidator(pattern=r'.*')

        self.assertTrue(validator('mr cactus is tevree'))

    def test_regex_validator_without_pattern_match(self):
        validator = RegexStringValidator()

        # per default the regex string matches everything
        self.assertEqual(validator.pattern, '.+')
        self.assertTrue(validator('mr cactus is tevree'))
        self.assertFalse(validator(''))

    def test_regex_validator_fails_on_none_value(self):
        validator = RegexStringValidator(pattern=r'.*')

        self.assertFalse(validator.is_valid(None))

    def test_regex_validator_complex_email_regex(self):
        validator = EmailValidator()

        self.assertTrue(validator.is_valid('support@ke-works.com'))
        self.assertFalse(validator.is_valid('___'))
        self.assertIsNone(validator.is_valid(None))
        self.assertFalse(validator.is_valid('user@domain'))


class TestOddEvenNumberValidator(SixTestCase):
    def test_even_number_validator_without_settings(self):
        validator = EvenNumberValidator()
        self.assertIsNone(validator.validate_json())
        self.assertIsInstance(validator.as_json(), dict)
        self.assertDictEqual(validator.as_json(), {'config': {}, 'vtype': 'evenNumberValidator'})

    def test_odd_number_validator_without_settings(self):
        validator = OddNumberValidator()
        self.assertIsNone(validator.validate_json())
        self.assertIsInstance(validator.as_json(), dict)
        self.assertDictEqual(validator.as_json(), {'config': {}, 'vtype': 'oddNumberValidator'})

    def test_even_number_validator_is_valid(self):
        validator = EvenNumberValidator()
        self.assertTrue(validator.is_valid(2))

    def test_odd_number_validator_is_valid(self):
        validator = OddNumberValidator()
        self.assertTrue(validator.is_valid(3))

    def test_even_number_validator_is_invalid(self):
        validator = EvenNumberValidator()
        self.assertFalse(validator.is_valid(3))

    def test_odd_number_validator_is_invalid(self):
        validator = OddNumberValidator()
        self.assertFalse(validator.is_valid(4))

    def test_even_number_validator_is_none(self):
        validator = EvenNumberValidator()
        self.assertIsNone(validator.is_valid(None))

    def test_odd_number_validator_is_none(self):
        validator = OddNumberValidator()
        self.assertIsNone(validator.is_valid(None))

    def test_even_number_validator_float_valid(self):
        validator = EvenNumberValidator()
        self.assertTrue(validator.is_valid(4.5))
        self.assertTrue(validator.is_valid(4.0))
        self.assertTrue(validator.is_valid(3.9999999999999999))  # rounding accuracy

    def test_odd_number_validator_float_valid(self):
        validator = OddNumberValidator()
        self.assertTrue(validator.is_valid(3.0))
        self.assertTrue(validator.is_valid(4.9999999999999999))  # rounding accuracy

    def test_even_number_validator_float_invalid(self):
        validator = EvenNumberValidator()
        self.assertFalse(validator.is_valid(3.99))
        self.assertFalse(validator.is_valid(5.5))

    def test_odd_number_validator_float_invalid(self):
        validator = OddNumberValidator()
        self.assertFalse(validator.is_valid(4.99))
        self.assertFalse(validator.is_valid(6.0))

    def test_even_number_validator_invalid_input(self):
        validator = EvenNumberValidator()
        self.assertFalse(validator.is_valid(dict()))
        self.assertFalse(validator.is_valid(list))
        self.assertFalse(validator.is_valid(set()))
        self.assertFalse(validator.is_valid(tuple()))
        self.assertFalse(validator.is_valid("3"))

    def test_odd_number_validator_invalid_input(self):
        validator = OddNumberValidator()
        self.assertFalse(validator.is_valid(dict()))
        self.assertFalse(validator.is_valid(list))
        self.assertFalse(validator.is_valid(set()))
        self.assertFalse(validator.is_valid(tuple()))
        self.assertFalse(validator.is_valid("3"))


class TestSingleReferenceValidator(SixTestCase):
    def test_singlereference_validator_without_settings(self):
        validator = SingleReferenceValidator()
        self.assertIsNone(validator.validate_json())
        self.assertIsInstance(validator.as_json(), dict)
        self.assertDictEqual(validator.as_json(), {'config': {}, 'vtype': 'singleReferenceValidator'})

    def test_singlereference_validator_is_valid(self):
        validator = SingleReferenceValidator()
        self.assertIsNone(validator.is_valid(None))
        self.assertTrue(validator.is_valid(list()))
        self.assertTrue(validator.is_valid(set()))
        self.assertTrue(validator.is_valid(tuple()))
        self.assertTrue(validator.is_valid(('first selection',)))

    def test_singlereference_validator_is_invalid(self):
        validator = SingleReferenceValidator()
        self.assertFalse(validator.is_valid(["first", "second"]))
        self.assertFalse(validator.is_valid((1, 2)))

    def test_singlerefence_validator_is_invalid_with_invalid_values(self):
        validator = SingleReferenceValidator()
        self.assertFalse(validator.is_valid("a string"))
        self.assertFalse(validator.is_valid(1.0))
        self.assertFalse(validator.is_valid(dict()))


class TestAlwaysAllowValidator(SixTestCase):
    def test_always_allow_validator_without_settings(self):
        validator = AlwaysAllowValidator()
        self.assertTrue(validator.is_valid('some text'))
        self.assertTrue(validator.is_valid(42))
        self.assertTrue(validator.is_valid(42.0))
        self.assertTrue(validator.is_valid(['a', 'b']))
        self.assertTrue(validator.is_valid(True))
        self.assertTrue(validator.is_valid(False))
        self.assertTrue(validator.is_valid(None))
        self.assertTrue(validator.is_valid({"a": "b"}))
        self.assertFalse(validator.is_invalid(None))
        self.assertTrue(validator.is_valid(list()))
        self.assertTrue(validator.is_valid(set()))
        self.assertTrue(validator.is_valid(tuple()))
        self.assertIsNone(validator.validate_json())


class TestFileSizeValidator(SixTestCase):
    def test_validator_valid_json_with_settings(self):
        validator = FileSizeValidator(max_size=100)
        self.assertIsNone(validator.validate_json())

    def test_validator_valid_json_without_settings(self):
        validator = FileSizeValidator()
        self.assertIsNone(validator.validate_json())

    def test_validator_valid_json_with_additional_arguments(self):
        validator = FileSizeValidator(max_size=100, another_argument=False)
        # another_argument is not found in the json
        validator.validate_json()
        validator.as_json()

    # noinspection PyTypeChecker
    def test_validator_invalid_arguments(self):
        with self.assertRaisesRegex(ValueError, 'should be a number'):
            FileSizeValidator(max_size=set())
        with self.assertRaisesRegex(ValueError, 'should be a number'):
            FileSizeValidator(max_size=list())
        with self.assertRaisesRegex(ValueError, 'should be a number'):
            FileSizeValidator(max_size=dict())
        with self.assertRaisesRegex(ValueError, 'should be a number'):
            FileSizeValidator(max_size=tuple())
        with self.assertRaisesRegex(ValueError, 'should be a number'):
            FileSizeValidator(max_size=tuple())
        with self.assertRaisesRegex(ValueError, 'should be a number'):
            FileSizeValidator(max_size='100')

    def test_filesizevalidator_being_valid(self):
        validator = FileSizeValidator(max_size=100)

        self.assertTrue(validator.is_valid(100))
        self.assertTrue(validator.is_valid(100.))
        self.assertTrue(validator.is_valid(99))
        self.assertTrue(validator.is_valid(0))

        self.assertTrue(validator.is_valid('text'))
        self.assertTrue(validator.is_valid(list()))
        self.assertTrue(validator.is_valid(tuple()))
        self.assertTrue(validator.is_valid(dict()))
        self.assertTrue(validator.is_valid(set()))

    def test_filesizevalidator_being_invalid(self):
        validator = FileSizeValidator(max_size=100)

        self.assertFalse(validator.is_valid(101))
        self.assertFalse(validator.is_valid(101.))
        self.assertFalse(validator.is_valid(-1))

    def test_filesizevalidator_being_none(self):
        validator = FileSizeValidator(max_size=100)

        self.assertIsNone(validator.is_valid(None))


class TestFileExtensionValidator(SixTestCase):
    def test_validator_valid_json_with_settings(self):
        validator = FileExtensionValidator(accept=[".csv"])
        self.assertIsNone(validator.validate_json())

    def test_validator_valid_json_without_settings(self):
        validator = FileExtensionValidator()
        self.assertIsNone(validator.validate_json())

    def test_fileextensionvalidator_on_extension(self):
        validator = FileExtensionValidator(accept=[".csv"])
        self.assertTrue(validator.is_valid('file.csv'))
        self.assertFalse(validator.is_valid('file.tsv'))
        self.assertFalse(validator.is_valid('file.txt'))

    def test_fileextensionvalidator_on_extensions(self):
        validator = FileExtensionValidator(accept=[".csv", ".pdf"])
        self.assertTrue(validator.is_valid('file.csv'))
        self.assertTrue(validator.is_valid('file.pdf'))
        self.assertFalse(validator.is_valid('file.docx'))

        with self.assertRaises(ValueError):
            # noinspection PyTypeChecker
            FileExtensionValidator(accept=True)

    def test_fileextensionvalidator_on_extensions_csv(self):
        validator = FileExtensionValidator(accept=".csv,.pdf")
        self.assertTrue(validator.is_valid('file.csv'))
        self.assertTrue(validator.is_valid('file.pdf'))
        self.assertFalse(validator.is_valid('file.docx'))

    def test_fileextensionvalidator_on_mimetype(self):
        validator = FileExtensionValidator(accept=["application/pdf"])
        self.assertTrue(validator.is_valid('file.pdf'))
        self.assertFalse(validator.is_valid('file.docx'))

    def test_fileextensionvalidator_on_expanded_mimetypes(self):
        validator = FileExtensionValidator(accept=["video/*"])
        self.assertTrue(validator.is_valid('file.mp4'))
        self.assertTrue(validator.is_valid('file.mov'))
        self.assertTrue(validator.is_valid('file.mpeg'))
        self.assertTrue(validator.is_valid('file.flv'))
        self.assertTrue(validator.is_valid('file.wmv'))
        self.assertTrue(validator.is_valid('file.webm'))

    def test_fileextensionvalidator_on_mixed_mode(self):
        validator = FileExtensionValidator(accept=[".csv", "application/pdf"])
        self.assertTrue(validator.is_valid('file.csv'))
        self.assertTrue(validator.is_valid('file.pdf'))
        self.assertFalse(validator.is_valid('file.docx'))

    def test_fileextensionvalidator_on_excel(self):
        validator = FileExtensionValidator(accept=[".xls", ".xlsx"])
        self.assertTrue(validator.is_valid('file.xls'))
        self.assertTrue(validator.is_valid('file.xlsx'))
        self.assertFalse(validator.is_valid('file.docx'))

    def test_fileextensionvalidator_being_none(self):
        validator = FileExtensionValidator(accept=["video/*"])

        self.assertIsNone(validator.is_valid(None))


class TestPropertyWithValidator(SixTestCase):

    def test_property_without_validator(self):
        prop = Property(json={}, client=None)
        self.assertIsNone(prop.is_valid)
        self.assertIsNone(prop.is_invalid)
        self.assertEqual(prop._validators, list())
        self.assertEqual(prop.validate(), list())

    def test_property_with_numeric_range_validator(self):
        prop_json = dict(
            value=1,
            value_options=dict(
                validators=[NumericRangeValidator(minvalue=0, maxvalue=10).as_json()]
            ))
        prop = Property(json=prop_json, client=None)
        self.assertTrue(prop.is_valid)
        self.assertFalse(prop.is_invalid)
        self.assertTrue(prop.validate())

    def test_property_with_numeric_range_validator_value_is_none(self):
        prop_json = dict(
            value=None,
            value_options=dict(
                validators=[NumericRangeValidator(minvalue=0, maxvalue=10).as_json()]
            ))
        prop = Property(json=prop_json, client=None)
        self.assertIsNone(prop.is_valid)
        self.assertIsNone(prop.is_invalid)
        self.assertListEqual([(None, "No reason")], prop.validate())

    def test_property_with_filesize_validator(self):
        prop_json = dict(
            value="attachments/12345678-1234-5678-1234-567812345678/some_file.txt",
            value_options=dict(
                validators=[FileSizeValidator(max_size=100).as_json()]
            ))
        prop = AttachmentProperty(json=prop_json, client=None)
        self.assertTrue(prop.is_valid)
        self.assertFalse(prop.is_invalid)
        self.assertTrue(prop.validate())

    def test_property_without_value_with_filesize_validator(self):
        prop_json = dict(
            value=None,
            value_options=dict(
                validators=[FileSizeValidator(max_size=100).as_json()]
            ))
        prop = AttachmentProperty(json=prop_json, client=None)
        self.assertIsNone(prop.is_valid)
        self.assertIsNone(prop.is_invalid)
        self.assertListEqual([(None, "No reason")], prop.validate())

    def test_property_with_fileextension_validator(self):
        prop_json = dict(
            value="attachments/12345678-1234-5678-1234-567812345678/some_file.txt",
            value_options=dict(
                validators=[FileExtensionValidator(accept=['.txt', 'application/pdf']).as_json()]
            ))
        prop = AttachmentProperty(json=prop_json, client=None)
        self.assertTrue(prop.is_valid)
        self.assertFalse(prop.is_invalid)
        self.assertTrue(prop.validate())

    def test_property_without_value_with_fileextension_validator(self):
        prop_json = dict(
            value=None,
            value_options=dict(
                validators=[FileExtensionValidator(accept=['.txt', 'application/pdf']).as_json()]
            ))
        prop = AttachmentProperty(json=prop_json, client=None)
        self.assertIsNone(prop.is_valid)
        self.assertIsNone(prop.is_invalid)
        self.assertListEqual([(None, "No reason")], prop.validate())


class TestPropertyWithValidatorFromLiveServer(TestBetamax):

    def setUp(self):
        super(TestPropertyWithValidatorFromLiveServer, self).setUp()
        self.part_model = self.project.model(name='Model')
        self.numeric_range_prop_model = self.part_model.add_property(name='numericrange_validatortest',
                                                                     property_type=PropertyType.FLOAT_VALUE)
        self.numeric_range_prop_model.validators = [NumericRangeValidator(min=0., max=42.)]
        self.part = self.project.part(name__startswith='Catalog').add(self.part_model, name='Model Instance for tests')
        self.numeric_range_prop_instance = self.part.property(name='numericrange_validatortest')

    def tearDown(self):
        self.numeric_range_prop_model.delete()
        self.part.delete()
        super(TestPropertyWithValidatorFromLiveServer, self).tearDown()

    def test_numeric_property_with_validator_parses(self):
        self.assertIsInstance(self.numeric_range_prop_instance._validators, list)
        self.assertIsInstance(self.numeric_range_prop_instance._validators[0], PropertyValidator)

    def test_numeric_property_add_requiredvalidator_on_model(self):
        # test
        validators = self.numeric_range_prop_model.validators
        validators.append(RequiredFieldValidator())
        self.numeric_range_prop_model.validators = validators

        for validator in self.numeric_range_prop_model.validators:
            self.assertIsInstance(validator, (NumericRangeValidator, RequiredFieldValidator))

    def test_numeric_property_add_requiredvalidator_on_instance(self):
        # test
        validators = self.numeric_range_prop_instance.validators
        validators.append(RequiredFieldValidator())

        with self.assertRaisesRegex(IllegalArgumentError, "To update the list of validators, it can only work "
                                                          "on `Property` of category 'MODEL'"):
            self.numeric_range_prop_instance.validators = validators

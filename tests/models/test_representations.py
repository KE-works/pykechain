from jsonschema import validate

from pykechain.enums import PropertyType, Multiplicity, LinkTargets, SelectListRepresentations
from pykechain.exceptions import IllegalArgumentError
from pykechain.models import AnyProperty
from pykechain.models.representations.representation_base import BaseRepresentation
from pykechain.models.representations.representations import ButtonRepresentation, LinkTarget, SignificantDigits, \
    DecimalPlaces, ThousandsSeparator
from pykechain.models.validators.validator_schemas import options_json_schema
from tests.classes import SixTestCase, TestBetamax


class TestRepresentationJSON(SixTestCase):
    def test_valid_button_representation_json(self):
        options = dict(
            representations=[dict(
                rtype='buttonRepresentation',
                config=dict(
                    buttonRepresentation="dropdown",
                )
            )]
        )
        validate(options_json_schema, options)


class TestSignificantDigitsLive(TestBetamax):
    """
    Specify these class attributes in every sub-class
    """
    property_type = PropertyType.FLOAT_VALUE  # type: PropertyType
    representation_class = SignificantDigits  # type: type(BaseRepresentation)
    value = 3
    new_value = 1

    test_model_name = '__test model for representations'
    test_prop_name = '__test property for representations'

    def setUp(self):
        super().setUp()
        product_root = self.project.model(name='Product')
        self.test_model = product_root.add_model(name=self.test_model_name, multiplicity=Multiplicity.ONE)
        self.prop_model = self.test_model.add_property(
            name=self.test_prop_name,
            property_type=self.property_type,
        )  # type: AnyProperty

    def tearDown(self):
        self.test_model.delete()
        super().tearDown()

    def test_getter(self):
        representations = self.prop_model.representations

        self.assertIsInstance(representations, list)
        self.assertTrue(all([isinstance(r, self.representation_class) for r in representations]))

    def test_setter(self):
        self.prop_model.representations = [
            self.representation_class(
                prop=self.prop_model,
                value=self.value,
            ),
        ]

        model = self.project.model(name=self.test_model_name)
        first_representation = model.property(name=self.test_prop_name).representations[0]

        self.assertIsInstance(first_representation, self.representation_class)
        self.assertTrue(first_representation.value == self.value)

    def test_set_value(self):
        # Make sure there is a representation object
        self.prop_model.representations = [
            self.representation_class(
                prop=self.prop_model,
                value=self.value,
            ),
        ]

        # Set new value
        first_repr = self.prop_model.representations[0]
        first_repr.value = self.new_value

        # Retrieve representation again
        model = self.project.model(name=self.test_model_name)
        first_representation = model.property(name=self.test_prop_name).representations[0]

        # testing
        self.assertEqual(first_repr.value, first_representation.value)

    def test_unsupported_value(self):

        with self.assertRaises(IllegalArgumentError):
            self.representation_class(
                prop=self.prop_model,
                value='Unexpected value',
            )


class TestThousandsSeparatorLive(TestSignificantDigitsLive):
    property_type = PropertyType.FLOAT_VALUE
    representation_class = ThousandsSeparator
    value = None
    new_value = None


class TestDecimalPlacesLive(TestSignificantDigitsLive):
    property_type = PropertyType.FLOAT_VALUE
    representation_class = DecimalPlaces
    value = 3
    new_value = 5


class TestLinkTargetLive(TestSignificantDigitsLive):
    property_type = PropertyType.LINK_VALUE
    representation_class = LinkTarget
    value = LinkTargets.SAME_TAB
    new_value = LinkTargets.NEW_TAB


class TestButtonRepresentationLive(TestSignificantDigitsLive):
    property_type = PropertyType.SINGLE_SELECT_VALUE
    representation_class = ButtonRepresentation
    value = SelectListRepresentations.CHECK_BOXES
    new_value = SelectListRepresentations.BUTTONS

    def setUp(self):
        super().setUp()
        self.prop_model.options = ['alpha', 'beta', 'gamma', 'omega']

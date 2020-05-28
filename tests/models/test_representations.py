from abc import abstractmethod, ABC

from jsonschema import validate

from pykechain.enums import PropertyType, Multiplicity, LinkTargets, SelectListRepresentations
from pykechain.exceptions import IllegalArgumentError
from pykechain.models import AnyProperty
from pykechain.models.representations.representation_base import BaseRepresentation
from pykechain.models.representations.representations import ButtonRepresentation, LinkTarget, SignificantDigits, \
    DecimalPlaces, ThousandsSeparator, CustomIconRepresentation
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


class _TestRepresentationLive(TestBetamax):
    """
    Specify these class attributes in every sub-class
    """
    representation_class = None  # type: type(BaseRepresentation)
    value = None
    new_value = None
    incorrect_value = None

    test_object_name = '__test object for representations'

    def setUp(self):
        super().setUp()
        self.obj = self._get_object()

    @abstractmethod
    def _get_object(self):
        pass

    def test_get_set(self):
        """Test representation accessor property of the Mixin class"""
        # setUp: set representations
        self.obj.representations = [
            self.representation_class(
                prop=self.obj,
                value=self.value,
            ),
        ]

        reloaded_obj = self.client.reload(self.obj)
        self.assertEqual(self.obj, reloaded_obj)

        # setUp: get representations
        first_representation = reloaded_obj.representations[0]

        self.assertIsInstance(first_representation, self.representation_class)
        self.assertEqual(first_representation.value, self.value)

    def test_set_value(self):
        """Test value accessor property of the Representation class"""
        # Make sure there is a representation object
        self.obj.representations = [
            self.representation_class(
                prop=self.obj,
                value=self.value,
            ),
        ]

        # Set new value via the representation object
        first_repr = self.obj.representations[0]
        first_repr.value = self.new_value

        # Retrieve representation again
        reloaded_obj = self.client.reload(self.obj)
        self.assertEqual(self.obj, reloaded_obj)

        first_representation = reloaded_obj.representations[0]

        # testing
        self.assertEqual(first_repr.value, first_representation.value)

    def test_unsupported_value(self):

        with self.assertRaises(IllegalArgumentError):
            self.representation_class(
                prop=self.obj,
                value=self.incorrect_value,
            )


class _TestPropertyRepresentation(_TestRepresentationLive, ABC):
    property_type = None
    test_model_name = '__test model for representations'
    test_model = None
    incorrect_value = 'Unsupported value'

    def tearDown(self):
        self.test_model.delete()
        super().tearDown()

    def _get_object(self):
        parent_model = self.project.model(name='Bike')
        self.test_model = parent_model.add_model(name=self.test_model_name, multiplicity=Multiplicity.ONE)
        obj = self.test_model.add_property(
            name=self.test_object_name,
            property_type=self.property_type,
        )  # type: AnyProperty
        return obj


class TestReprSignificantDigits(_TestPropertyRepresentation):
    property_type = PropertyType.FLOAT_VALUE
    representation_class = SignificantDigits
    value = 3
    new_value = 1


class TestReprThousandsSeparator(_TestPropertyRepresentation):
    property_type = PropertyType.FLOAT_VALUE
    representation_class = ThousandsSeparator
    value = None
    new_value = None


class TestReprDecimalPlaces(_TestPropertyRepresentation):
    property_type = PropertyType.FLOAT_VALUE
    representation_class = DecimalPlaces
    value = 3
    new_value = 5


class TestReprLinkTarget(_TestPropertyRepresentation):
    property_type = PropertyType.LINK_VALUE
    representation_class = LinkTarget
    value = LinkTargets.SAME_TAB
    new_value = LinkTargets.NEW_TAB


class TestReprButton(_TestPropertyRepresentation):
    property_type = PropertyType.SINGLE_SELECT_VALUE
    representation_class = ButtonRepresentation
    value = SelectListRepresentations.CHECK_BOXES
    new_value = SelectListRepresentations.BUTTONS

    def setUp(self):
        super().setUp()
        self.obj.options = ['alpha', 'beta', 'gamma', 'omega']


class _TestCustomIconRepresentation(_TestRepresentationLive, ABC):
    representation_class = CustomIconRepresentation
    value = 'university'
    new_value = 'bat'
    incorrect_value = ['must be a string']


class TestReprActivity(_TestCustomIconRepresentation):

    def _get_object(self):
        return self.project.create_activity(name=self.test_object_name)


class TestReprScope(_TestCustomIconRepresentation):

    def _get_object(self):
        return self.client.create_scope(name=self.test_object_name)

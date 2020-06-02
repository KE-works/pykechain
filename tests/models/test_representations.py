from abc import abstractmethod, ABC
from typing import Union

from jsonschema import validate

from pykechain.enums import PropertyType, Multiplicity, LinkTargets, SelectListRepresentations, FontAwesomeMode
from pykechain.exceptions import IllegalArgumentError, APIError
from pykechain.models import AnyProperty, Property2, Scope2, Activity2, SelectListProperty2
from pykechain.models.representations.representation_base import BaseRepresentation
from pykechain.models.representations.representations import ButtonRepresentation, LinkTarget, SignificantDigits, \
    DecimalPlaces, ThousandsSeparator, CustomIconRepresentation
from pykechain.models.validators.validator_schemas import options_json_schema
from tests.classes import SixTestCase, TestBetamax

representation_config = dict(
    rtype='buttonRepresentation',
    config=dict(
        buttonRepresentation="dropdown",
    )
)
options = dict(
    representations=[representation_config],
)


class TestRepresentationJSON(SixTestCase):

    def test_valid_button_representation_json(self):
        validate(options_json_schema, options)


class TestRepresentation(SixTestCase):
    def test_create(self):
        representation = BaseRepresentation()

        self.assertIsInstance(representation, BaseRepresentation)

    def test_create_with_value(self):
        representation = DecimalPlaces(value=3)

        self.assertEqual(3, representation.value)

    def test_create_with_object(self):
        empty_prop = Property2(json={}, client=None)
        representation = ButtonRepresentation(empty_prop)

        self.assertIsInstance(representation, ButtonRepresentation)

    def test_parse(self):
        empty_slp = SelectListProperty2(json={'value_options': {}}, client=None)
        BaseRepresentation.parse(obj=empty_slp, json=representation_config)

    def test_parse_incorrect_rtype(self):
        no_rtype_config = dict(
            config=dict(
                buttonRepresentation="dropdown",
            )
        )
        with self.assertRaises(ValueError):
            BaseRepresentation.parse(obj=None, json=no_rtype_config)

    def test_parse_unknown_rtype(self):
        no_rtype_config = dict(
            rtype='Not a representation type',
            config=dict(
                buttonRepresentation="dropdown",
            )
        )
        with self.assertRaises(TypeError):
            BaseRepresentation.parse(obj=None, json=no_rtype_config)

    def test_component_invalid_object(self):
        empty_activity = Activity2(json={'id': '1234567890'}, client=None)
        representation = ThousandsSeparator(empty_activity)

        with self.assertRaises(IllegalArgumentError):
            empty_activity.representations = [representation]

    def test_component_invalid_property_type(self):
        empty_prop = Property2(json={'id': '1234567890', 'category': 'MODEL'}, client=None)
        representation = ThousandsSeparator(empty_prop)
        representation.rtype = 'Broken rtype'

        with self.assertRaises(IllegalArgumentError):
            empty_prop.representations = [representation]

    def test_component_not_a_list(self):
        empty_activity = Activity2(json={}, client=None)

        with self.assertRaises(IllegalArgumentError):
            empty_activity.representations = 'Howdy!'

    def test_component_not_a_representation(self):
        empty_activity = Activity2(json={}, client=None)

        with self.assertRaises(IllegalArgumentError):
            empty_activity.representations = ['Howdy again!']


class Bases:
    """
    Wrapping private test classes in this Base class allows some inheritance mechanisms to be used.

    If the _Test...() classes would not be wrapped, the test framework would try to run these abstract classes.
    """

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
            self.obj.representations = [
                self.representation_class(
                    prop=self.obj,
                    value=self.value,
                ),
            ]

        def tearDown(self):
            if self.obj:
                try:
                    self.obj.delete()
                except APIError:
                    pass
            super().tearDown()

        @abstractmethod
        def _get_object(self) -> Union[Property2, Scope2, Activity2]:
            pass

        def test_get_set(self):
            """Test representation accessor property of the Mixin class"""
            reloaded_obj = self.client.reload(self.obj)
            self.assertEqual(self.obj, reloaded_obj)

            # setUp: get representations
            first_representation = reloaded_obj.representations[0]

            self.assertIsInstance(first_representation, self.representation_class)
            self.assertEqual(self.value, first_representation.value)

        def test_set_value(self):
            """Test value accessor property of the Representation class"""
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

    class _TestPropertyRepresentation(_TestRepresentationLive):
        property_type = None
        test_model_name = '__test model for representations'
        test_model = None
        incorrect_value = 'Unsupported value'

        def tearDown(self):
            if self.test_model:
                try:
                    self.test_model.delete()
                except APIError:
                    pass
            super().tearDown()

        def _get_object(self):
            parent_model = self.project.model(name='Bike')
            self.test_model = parent_model.add_model(name=self.test_model_name, multiplicity=Multiplicity.ONE)
            obj = self.test_model.add_property(
                name=self.test_object_name,
                property_type=self.property_type,
            )  # type: AnyProperty
            return obj

    class _TestCustomIconRepresentation(_TestRepresentationLive, ABC):
        representation_class = CustomIconRepresentation
        value = 'university'
        new_value = 'bat'
        incorrect_value = ['must be a string']

        def test_set_mode(self):
            representation = self.obj.representations[0]  # type: CustomIconRepresentation

            # Set mode
            representation.display_mode = FontAwesomeMode.SOLID

            reloaded_obj = self.client.reload(obj=self.obj)
            reloaded_repr = reloaded_obj.representations[0]

            # Test get of mode
            self.assertEqual(representation.display_mode, reloaded_repr.display_mode)

        def test_set_mode_incorrect(self):
            representation = self.obj.representations[0]  # type: CustomIconRepresentation

            with self.assertRaises(IllegalArgumentError):
                representation.display_mode = 'fancy colors'


class TestReprSignificantDigits(Bases._TestPropertyRepresentation):
    property_type = PropertyType.FLOAT_VALUE
    representation_class = SignificantDigits
    value = 3
    new_value = 1


class TestReprThousandsSeparator(Bases._TestPropertyRepresentation):
    property_type = PropertyType.FLOAT_VALUE
    representation_class = ThousandsSeparator
    value = None
    new_value = None


class TestReprDecimalPlaces(Bases._TestPropertyRepresentation):
    property_type = PropertyType.FLOAT_VALUE
    representation_class = DecimalPlaces
    value = 3
    new_value = 5


class TestReprLinkTarget(Bases._TestPropertyRepresentation):
    property_type = PropertyType.LINK_VALUE
    representation_class = LinkTarget
    value = LinkTargets.SAME_TAB
    new_value = LinkTargets.NEW_TAB


class TestReprButton(Bases._TestPropertyRepresentation):
    property_type = PropertyType.SINGLE_SELECT_VALUE
    representation_class = ButtonRepresentation
    value = SelectListRepresentations.CHECK_BOXES
    new_value = SelectListRepresentations.BUTTONS

    def setUp(self):
        super().setUp()
        self.obj.options = ['alpha', 'beta', 'gamma', 'omega']


class TestReprActivity(Bases._TestCustomIconRepresentation):

    def _get_object(self):
        return self.project.create_activity(name=self.test_object_name)


class TestReprScope(Bases._TestCustomIconRepresentation):

    def _get_object(self):
        return self.client.create_scope(name=self.test_object_name)

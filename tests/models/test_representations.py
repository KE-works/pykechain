from abc import ABC, abstractmethod
from typing import Union
from unittest import TestCase

from jsonschema import validate

from pykechain.enums import (
    FontAwesomeMode,
    GeoCoordinateConfig,
    LinkTargets,
    Multiplicity,
    PropertyType,
    SelectListRepresentations,
)
from pykechain.exceptions import APIError, IllegalArgumentError
from pykechain.models import Activity, AnyProperty, Property, Scope, SelectListProperty
from pykechain.models.representations.representation_base import BaseRepresentation
from pykechain.models.representations.representations import (
    Autofill,
    ButtonRepresentation,
    CameraScannerInputRepresentation,
    CustomIconRepresentation,
    DecimalPlaces,
    GeoCoordinateRepresentation,
    LinkTarget,
    SignificantDigits,
    ThousandsSeparator,
    UsePropertyNameRepresentation,
)
from pykechain.models.validators.validator_schemas import options_json_schema
from tests.classes import TestBetamax

representation_config = dict(
    rtype="buttonRepresentation",
    config=dict(
        buttonRepresentation="dropdown",
    ),
)
options = dict(
    representations=[representation_config],
)


class TestRepresentationJSON(TestCase):
    def test_valid_button_representation_json(self):
        validate(options_json_schema, options)


class TestRepresentation(TestCase):
    def test_create(self):
        representation = BaseRepresentation()

        self.assertIsInstance(representation, BaseRepresentation)

    def test_create_with_value(self):
        representation = DecimalPlaces(value=3)

        self.assertEqual(3, representation.value)

    def test_create_with_object(self):
        empty_prop = Property(json={}, client=None)
        representation = ButtonRepresentation(empty_prop)

        self.assertIsInstance(representation, ButtonRepresentation)

    def test_parse(self):
        empty_slp = SelectListProperty(json={"value_options": {}}, client=None)
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
            rtype="Not a representation type",
            config=dict(
                buttonRepresentation="dropdown",
            ),
        )
        with self.assertRaises(TypeError):
            BaseRepresentation.parse(obj=None, json=no_rtype_config)

    def test_component_invalid_object(self):
        empty_activity = Activity(json={"id": "1234567890"}, client=None)
        representation = ThousandsSeparator(empty_activity)

        with self.assertRaises(IllegalArgumentError):
            empty_activity.representations = [representation]

    def test_component_invalid_property_type(self):
        empty_prop = Property(
            json={"id": "1234567890", "category": "MODEL"}, client=None
        )
        representation = ThousandsSeparator(empty_prop)
        representation.rtype = "Broken rtype"

        with self.assertRaises(IllegalArgumentError):
            empty_prop.representations = [representation]

    def test_component_not_a_list(self):
        empty_activity = Activity(json={}, client=None)

        with self.assertRaises(IllegalArgumentError):
            empty_activity.representations = "Howdy!"

    def test_component_not_a_representation(self):
        empty_activity = Activity(json={}, client=None)

        with self.assertRaises(IllegalArgumentError):
            empty_activity.representations = ["Howdy again!"]


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

        test_object_name = "__test object for representations"

        def setUp(self):
            super().setUp()
            self.obj = self._get_object()
            try:
                self.obj.representations = [
                    self.representation_class(
                        obj=self.obj,
                        value=self.value,
                    ),
                ]
            except Exception as e:
                self.obj.part.delete()
                raise e

        def tearDown(self):
            if self.obj:
                try:
                    self.obj.delete()
                except APIError:
                    pass
            super().tearDown()

        @abstractmethod
        def _get_object(self) -> Union[Property, Scope, Activity]:
            pass

        def test_create_with_prop(self):
            representation = self.representation_class(prop=self.obj, value=self.value)

            self.assertIsInstance(representation, self.representation_class)

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
                    obj=self.obj,
                    value=self.incorrect_value,
                )

    class _TestPropertyRepresentation(_TestRepresentationLive):
        property_type = None
        test_model_name = "__test model for representations"
        test_model = None
        incorrect_value = "Unsupported value"

        def tearDown(self):
            if self.test_model:
                try:
                    self.test_model.delete()
                except APIError:
                    pass
            super().tearDown()

        def _get_object(self):
            parent_model = self.project.model(name="Bike")
            self.test_model = parent_model.add_model(
                name=self.test_model_name, multiplicity=Multiplicity.ONE
            )
            obj = self.test_model.add_property(
                name=self.test_object_name,
                property_type=self.property_type,
            )  # type: AnyProperty
            return obj

    class _TestCustomIconRepresentation(_TestRepresentationLive, ABC):
        representation_class = CustomIconRepresentation
        value = "university"
        new_value = "bat"
        incorrect_value = ["must be a string"]

        def test_set_mode(self):
            representation = self.obj.representations[
                0
            ]  # type: CustomIconRepresentation

            # Set mode
            representation.display_mode = FontAwesomeMode.SOLID

            reloaded_obj = self.client.reload(obj=self.obj)
            reloaded_repr = reloaded_obj.representations[0]

            # Test get of mode
            self.assertEqual(representation.display_mode, reloaded_repr.display_mode)

        def test_set_mode_incorrect(self):
            representation = self.obj.representations[
                0
            ]  # type: CustomIconRepresentation

            with self.assertRaises(IllegalArgumentError):
                representation.display_mode = "fancy colors"


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


class TestGeocoordinateRepresentation(Bases._TestPropertyRepresentation):
    property_type = PropertyType.GEOJSON_VALUE
    representation_class = GeoCoordinateRepresentation
    value = GeoCoordinateConfig.RD_AMERSFOORT
    new_value = GeoCoordinateConfig.APPROX_ADDRESS


class TestReprButton(Bases._TestPropertyRepresentation):
    property_type = PropertyType.SINGLE_SELECT_VALUE
    representation_class = ButtonRepresentation
    value = SelectListRepresentations.CHECK_BOXES
    new_value = SelectListRepresentations.BUTTONS

    def setUp(self):
        super().setUp()
        self.obj.options = ["alpha", "beta", "gamma", "omega"]


class TestUsePropertyNameRepresentationForPartReferences(
    Bases._TestPropertyRepresentation
):
    property_type = PropertyType.REFERENCES_VALUE
    representation_class = UsePropertyNameRepresentation
    value = True
    new_value = False

    def test_empty_config_value(self):
        # get the representation on the object
        repr = self.obj.representations[-1]

        # set it as an empty config object
        repr_json = repr.as_json()
        repr_json["config"] = {}
        new_value_options = dict(representations=[repr_json])
        # edit options directly otherwise it would not 'stick'
        self.obj.edit(options=new_value_options)

        # reload from server the representations
        self.obj.refresh()
        repr = self.obj.representations[-1]

        # check sanity of the representation with the empty object.
        self.assertDictEqual(self.obj._options.get("representations")[0], repr_json)
        self.assertEqual(type(repr), UsePropertyNameRepresentation)
        self.assertIsNone(repr.value)


class TestUsePropertyNameRepresentationForUserReferences(
    Bases._TestPropertyRepresentation
):
    property_type = PropertyType.USER_REFERENCES_VALUE
    representation_class = UsePropertyNameRepresentation
    value = True
    new_value = False


class TestUsePropertyNameRepresentationForScopeReferences(
    Bases._TestPropertyRepresentation
):
    property_type = PropertyType.SCOPE_REFERENCES_VALUE
    representation_class = UsePropertyNameRepresentation
    value = True
    new_value = False


class TestUsePropertyNameRepresentationForServiceReferences(
    Bases._TestPropertyRepresentation
):
    property_type = PropertyType.SERVICE_REFERENCES_VALUE
    representation_class = UsePropertyNameRepresentation
    value = True
    new_value = False


class TestUsePropertyNameRepresentationForActivityReferences(
    Bases._TestPropertyRepresentation
):
    property_type = PropertyType.ACTIVITY_REFERENCES_VALUE
    representation_class = UsePropertyNameRepresentation
    value = True
    new_value = False


class TestUseCameraScannerInputRepresentationForCharProperties(
    Bases._TestPropertyRepresentation
):
    property_type = PropertyType.CHAR_VALUE
    representation_class = CameraScannerInputRepresentation
    value = True
    new_value = False


class TestUseCameraScannerInputRepresentationForTextAreaCharProperties(
    Bases._TestPropertyRepresentation
):
    property_type = PropertyType.TEXT_VALUE
    representation_class = CameraScannerInputRepresentation
    value = True
    new_value = False


class TestUseCameraScannerInputRepresentationForFloatAreaProperties(
    Bases._TestPropertyRepresentation
):
    property_type = PropertyType.FLOAT_VALUE
    representation_class = CameraScannerInputRepresentation
    value = True
    new_value = False


class TestUseCameraScannerInputRepresentationForIntegerAreaProperties(
    Bases._TestPropertyRepresentation
):
    property_type = PropertyType.INT_VALUE
    representation_class = CameraScannerInputRepresentation
    value = True
    new_value = False


class TestReprAutofill(Bases._TestPropertyRepresentation):
    property_type = PropertyType.DATETIME_VALUE
    representation_class = Autofill
    value = False
    new_value = True


class TestReprAutofillUser(Bases._TestPropertyRepresentation):
    property_type = PropertyType.USER_REFERENCES_VALUE
    representation_class = Autofill
    value = False
    new_value = True


class TestReprActivity(Bases._TestCustomIconRepresentation):
    def _get_object(self):
        return self.project.create_activity(name=self.test_object_name)


class TestReprScope(Bases._TestCustomIconRepresentation):
    def _get_object(self):
        return self.client.create_scope(name=self.test_object_name)

from unittest import TestCase

from pykechain.enums import FilterType
from pykechain.exceptions import IllegalArgumentError
from pykechain.models import PropertyValueFilter
from pykechain.models.value_filter import ScopeFilter
from tests.classes import TestBetamax


class TestPropertyValueFilter(TestBetamax):

    def setUp(self):
        super().setUp()

        self.bike = self.project.product_root_model("Bike")

        self.filter = PropertyValueFilter(
            property_model=self.bike.property(name="Gears"),
            value=15,
            filter_type=FilterType.GREATER_THAN_EQUAL,
        )

    # noinspection PyTypeChecker
    def test_creation(self):
        with self.assertRaises(IllegalArgumentError):
            PropertyValueFilter(property_model=self.bike, value=15, filter_type=FilterType.EXACT)

        with self.assertRaises(IllegalArgumentError):
            PropertyValueFilter(property_model=self.bike.property(name="Gears"), value=15, filter_type="this one plz")

    def test_repr(self):
        representation = self.filter.__repr__()

        self.assertIsInstance(representation, str)

    def test_format(self):
        string = self.filter.format()

        self.assertIsInstance(string, str)
        self.assertIn(":", string)

    def test_validate(self):
        self.filter.validate(part_model=self.bike)

        with self.assertRaises(IllegalArgumentError):
            self.filter.validate(part_model="Not a part model")

        bike_instance = self.bike.instance()
        property_instance = bike_instance.property(name="Gears")
        invalid_filter = PropertyValueFilter(
            property_model=property_instance,
            value=15,
            filter_type=FilterType.GREATER_THAN_EQUAL,
        )

        with self.assertRaises(IllegalArgumentError, msg="Property instance is not allowed"):
            invalid_filter.validate(part_model=bike_instance)

        with self.assertRaises(IllegalArgumentError, msg="Property instance should not match the bike model"):
            invalid_filter.validate(part_model=self.bike)

        boolean = self.bike.property(name="Sale?")
        boolean_filter = PropertyValueFilter(
            property_model=boolean,
            value=False,
            filter_type=FilterType.CONTAINS,
        )

        with self.assertWarns(Warning, msg="Using any filter but EXACT should be warned against"):
            boolean_filter.validate(part_model=self.bike)

        self.assertIn("false", boolean_filter.format(), msg="Boolean value should have been parsed to a string")

    def test_parse_options(self):
        for options in [
            dict(),
            dict(prefilters=dict()),
            dict(prefilters=dict(property_value="")),
        ]:
            with self.subTest():
                prefilters = PropertyValueFilter.parse_options(options=options)

                self.assertIsInstance(prefilters, list)
                self.assertEqual(0, len(prefilters))

        prefilters = PropertyValueFilter.parse_options(
            dict(prefilters=dict(property_value=self.filter.format()))
        )

        self.assertIsInstance(prefilters, list)
        self.assertEqual(1, len(prefilters))

    def test__eq__(self):
        second_filter = PropertyValueFilter(self.bike.property("Gears"), 15, FilterType.GREATER_THAN_EQUAL)
        third_filter = PropertyValueFilter(self.bike.property("Gears"), 16, FilterType.GREATER_THAN_EQUAL)
        fourth_filter = PropertyValueFilter(self.bike.property("Total height"), 15, FilterType.GREATER_THAN_EQUAL)
        fifth_filter = PropertyValueFilter(self.bike.property("Gears"), 15, FilterType.LOWER_THAN_EQUAL)

        self.assertEqual(self.filter, second_filter)
        self.assertNotEqual(self.filter, "Coffee filter")
        self.assertNotEqual(self.filter, third_filter)
        self.assertNotEqual(self.filter, fourth_filter)
        self.assertNotEqual(self.filter, fifth_filter)


class TestScopeFilter(TestCase):

    def setUp(self) -> None:
        self.filter = ScopeFilter(tag="Calculation")

    def test__repr__(self):
        representation = self.filter.__repr__()

        self.assertIsInstance(representation, str)

    def test__eq__(self):
        second_filter = ScopeFilter("Calculation")
        third_filter = ScopeFilter("Not a calculation")

        self.assertEqual(self.filter, second_filter)
        self.assertNotEqual(self.filter, third_filter)

    def test_format(self):
        string = self.filter.format()

        self.assertIsInstance(string, str)

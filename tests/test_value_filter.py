import datetime
from unittest import TestCase

import pytz

from pykechain.enums import FilterType, ScopeStatus
from pykechain.exceptions import IllegalArgumentError
from pykechain.models import PropertyValueFilter
from pykechain.models.value_filter import ScopeFilter
from pykechain.models.widgets.enums import MetaWidget
from tests.classes import TestBetamax

TIMESTAMP = datetime.datetime(year=2020, month=1, day=1, tzinfo=pytz.UTC)
TIMESTAMP_2 = datetime.datetime(year=2020, month=5, day=1, tzinfo=pytz.UTC)


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

    def test_write_options(self):
        options_dict = PropertyValueFilter.write_options(filters=[self.filter])

        self.assertIsInstance(options_dict, dict)

        with self.assertRaises(IllegalArgumentError):
            ScopeFilter.write_options(filters=[self.filter])

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


class BaseTest(object):
    class _TestScopeFilter(TestCase):

        VALUE = None
        VALUE_2 = None
        INVALID_VALUE = None
        FIELD = None
        ATTR = None

        @classmethod
        def setUpClass(cls) -> None:
            super().setUpClass()
            if cls.VALUE == cls.VALUE_2:  # pragma: no cover
                raise ValueError("Test needs 2 different values ({}, {})".format(cls.VALUE, cls.VALUE_2))

        def setUp(self) -> None:
            super().setUp()
            self.filter = ScopeFilter(**{self.ATTR: self.VALUE})

        def test__repr__(self):
            representation = self.filter.__repr__()

            self.assertIsInstance(representation, str)

        def test__eq__(self):
            second_filter = ScopeFilter(**{self.ATTR: self.VALUE})
            third_filter = ScopeFilter(**{self.ATTR: self.VALUE_2})

            self.assertEqual(self.filter, second_filter)
            self.assertNotEqual(self.filter, third_filter)

        def test_write_options(self):
            filter_2 = ScopeFilter(**{self.ATTR: self.VALUE_2})
            filters = [self.filter, filter_2]

            options_dict = ScopeFilter.write_options(filters=filters)

            self.assertIsInstance(options_dict, dict)

            with self.assertRaises(IllegalArgumentError):
                PropertyValueFilter.write_options(filters=[self.filter])

        def test_parse_options(self):
            options = ScopeFilter.write_options(filters=[self.filter])

            scope_filters = ScopeFilter.parse_options(options=options)

            self.assertTrue(scope_filters)
            self.assertIsInstance(scope_filters, list)
            self.assertTrue(all(isinstance(sf, ScopeFilter) for sf in scope_filters))

        def test_creation(self):
            if self.INVALID_VALUE is not None:
                with self.assertRaises(IllegalArgumentError):
                    ScopeFilter(**{self.ATTR: self.INVALID_VALUE})

            with self.assertRaises(IllegalArgumentError):
                ScopeFilter(tag="My scope tag", status=ScopeStatus.ACTIVE)


class TestScopeFilterName(BaseTest._TestScopeFilter):
    VALUE = "My project"
    VALUE_2 = "Not my project"
    INVALID_VALUE = 3
    FIELD = "name__icontains"
    ATTR = "name"


class TestScopeFilterStatus(BaseTest._TestScopeFilter):
    VALUE = ScopeStatus.CLOSED
    VALUE_2 = ScopeStatus.ACTIVE
    INVALID_VALUE = "Just a fleshwound"
    FIELD = "status__in"
    ATTR = "status"


class TestScopeFilterDueDateGTE(BaseTest._TestScopeFilter):
    VALUE = TIMESTAMP
    VALUE_2 = TIMESTAMP_2
    INVALID_VALUE = 3
    FIELD = "due_date__gte"
    ATTR = "due_date_gte"

    
class TestScopeFilterDueDateLTE(BaseTest._TestScopeFilter):
    VALUE = TIMESTAMP
    VALUE_2 = TIMESTAMP_2
    INVALID_VALUE = 3
    FIELD = "due_date__lte"
    ATTR = "due_date_lte"

    
class TestScopeFilterStartDateGTE(BaseTest._TestScopeFilter):
    VALUE = TIMESTAMP
    VALUE_2 = TIMESTAMP_2
    INVALID_VALUE = 3
    FIELD = "start_date__gte"
    ATTR = "start_date_gte"

    
class TestScopeFilterStartDateLTE(BaseTest._TestScopeFilter):
    VALUE = TIMESTAMP
    VALUE_2 = TIMESTAMP_2
    INVALID_VALUE = 3
    FIELD = "start_date__lte"
    ATTR = "start_date_lte"


class TestScopeFilterProgressGTE(BaseTest._TestScopeFilter):
    VALUE = 0.2
    VALUE_2 = 0.3
    INVALID_VALUE = "completed"
    FIELD = "progress__gte"
    ATTR = "progress_gte"


class TestScopeFilterProgressLTE(BaseTest._TestScopeFilter):
    VALUE = 0.2
    VALUE_2 = 0.3
    INVALID_VALUE = "completed"
    FIELD = "progress__lte"
    ATTR = "progress_lte"


class TestScopeFilterTag(BaseTest._TestScopeFilter):
    VALUE = "Calculation"
    VALUE_2 = "Not a calculation"
    INVALID_VALUE = 3
    FIELD = "tags__contains"
    ATTR = "tag"


class TestScopeFilterTeam(BaseTest._TestScopeFilter):
    VALUE = "a2a0631b-d771-4807-bd22-c5ccde581e79"
    VALUE_2 = "9bab05df-5597-4a7a-af65-73cc65fee22a"
    INVALID_VALUE = 3
    FIELD = "team__in"
    ATTR = "team"


class TestScopeFilterUnknown(BaseTest._TestScopeFilter):
    VALUE = 1
    VALUE_2 = 2
    INVALID_VALUE = None
    FIELD = "new_filter__type"
    ATTR = "new_filter_type"

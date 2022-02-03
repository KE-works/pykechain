import datetime
import urllib
import warnings
from unittest import TestCase

import pytz

from pykechain.enums import (
    FilterType,
    ScopeStatus,
    Multiplicity,
    PropertyType,
    ActivityType,
    ActivityRootNames,
)
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

        self.new_part = self.bike.add_model(
            name="__TEST_PART__", multiplicity=Multiplicity.ZERO_MANY
        )
        self.new_test_property = self.new_part.add_property(
            name="__test_propERTY__", property_type=PropertyType.TEXT_VALUE
        )

    def tearDown(self):
        self.new_part.delete()
        super().tearDown()

    # noinspection PyTypeChecker
    def test_creation(self):
        with self.assertRaises(IllegalArgumentError):
            PropertyValueFilter(property_model=self.bike, value=15, filter_type=FilterType.EXACT)

        with self.assertRaises(IllegalArgumentError):
            PropertyValueFilter(
                property_model=self.bike.property(name="Gears"),
                value=15,
                filter_type="this one plz",
            )

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

        with self.assertRaises(
            IllegalArgumentError, msg="Property instance should not match the bike model"
        ):
            invalid_filter.validate(part_model=self.bike)

        boolean = self.bike.property(name="Sale?")
        boolean_filter = PropertyValueFilter(
            property_model=boolean,
            value=False,
            filter_type=FilterType.CONTAINS,
        )

        with self.assertWarns(Warning, msg="Using any filter but EXACT should be warned against"):
            boolean_filter.validate(part_model=self.bike)

        self.assertIn(
            "false",
            boolean_filter.format(),
            msg="Boolean value should have been parsed to a string",
        )

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
        second_filter = PropertyValueFilter(
            self.bike.property("Gears"), 15, FilterType.GREATER_THAN_EQUAL
        )
        third_filter = PropertyValueFilter(
            self.bike.property("Gears"), 16, FilterType.GREATER_THAN_EQUAL
        )
        fourth_filter = PropertyValueFilter(
            self.bike.property("Total height"), 15, FilterType.GREATER_THAN_EQUAL
        )
        fifth_filter = PropertyValueFilter(
            self.bike.property("Gears"), 15, FilterType.LOWER_THAN_EQUAL
        )

        self.assertEqual(self.filter, second_filter)
        self.assertNotEqual(self.filter, "Coffee filter")
        self.assertNotEqual(self.filter, third_filter)
        self.assertNotEqual(self.filter, fourth_filter)
        self.assertNotEqual(self.filter, fifth_filter)


class TestPropertyFilterAllPropertyTypes(TestBetamax):
    def setUp(self):
        super().setUp()

        self.bike = self.project.product_root_model("Bike")
        self.bike_instance = self.bike.instance()
        self.root = self.project.activity(name=ActivityRootNames.WORKFLOW_ROOT)
        self.wheel = self.project.model(name="Wheel")
        self.test_activity = self.project.create_activity(
            name="__TEST__FILTERS__",
            activity_type=ActivityType.TASK,
        )
        self.wm = self.test_activity.widgets()
        self.prop_test_name = "__PROP TEST"
        self.new_wheel = self.bike_instance.add(model=self.wheel, name="Wheel, Wheel")
        self.new_part = self.bike.add_model(
            name="__TEST_PART__", multiplicity=Multiplicity.ZERO_MANY
        )
        self.filter_types = FilterType.values()

    def tearDown(self):
        if self.test_activity:
            self.test_activity.delete()
        if self.new_part:
            self.new_part.delete()
        if self.new_wheel:
            self.new_wheel.delete()
        super().tearDown()

    def test_text_property_filter_in_grid(self):
        filter_value = "sample"
        test_prop = self.new_part.add_property(
            name=self.prop_test_name, property_type=PropertyType.TEXT_VALUE
        )
        self.bike_instance.add_with_properties(
            model=self.new_part, update_dict={test_prop.id: "sample text"}
        )
        self.bike_instance.add_with_properties(
            model=self.new_part, update_dict={test_prop.id: "just text"}
        )
        with warnings.catch_warnings(record=True) as w:
            for filter_type in self.filter_types:
                prefilter = PropertyValueFilter(
                    property_model=test_prop, value=filter_value, filter_type=filter_type
                )
                widget = self.wm.add_filteredgrid_widget(
                    title=filter_type,
                    part_model=self.new_part,
                    readable_models=list(),
                    writable_models=[test_prop],
                    custom_height=300,
                    parent_instance=self.bike_instance,
                    prefilters=[prefilter],
                )
                self.assertEqual(
                    widget.meta.get("prefilters").get("property_value"),
                    f"{test_prop.id}:{filter_value}:{filter_type}",
                )
            self.assertEqual(len(w), 4)

    def test_multi_test_property_filter_in_grid(self):
        filter_value = "sample"
        test_prop = self.new_part.add_property(
            name=self.prop_test_name, property_type=PropertyType.CHAR_VALUE
        )
        self.bike_instance.add_with_properties(
            model=self.new_part, update_dict={test_prop.id: "sample text"}
        )
        self.bike_instance.add_with_properties(
            model=self.new_part, update_dict={test_prop.id: "just text"}
        )
        with warnings.catch_warnings(record=True) as w:
            for filter_type in self.filter_types:
                prefilter = PropertyValueFilter(
                    property_model=test_prop, value=filter_value, filter_type=filter_type
                )
                widget = self.wm.add_filteredgrid_widget(
                    title=filter_type,
                    part_model=self.new_part,
                    readable_models=list(),
                    writable_models=[test_prop],
                    custom_height=300,
                    parent_instance=self.bike_instance,
                    prefilters=[prefilter],
                )
                self.assertEqual(
                    widget.meta.get("prefilters").get("property_value"),
                    f"{test_prop.id}:{filter_value}:{filter_type}",
                )
            self.assertEqual(len(w), 4)

    def test_int_property_filter_in_grid(self):
        filter_value = 17
        test_prop = self.new_part.add_property(
            name=self.prop_test_name, property_type=PropertyType.INT_VALUE
        )
        self.bike_instance.add_with_properties(model=self.new_part, update_dict={test_prop.id: 15})
        self.bike_instance.add_with_properties(model=self.new_part, update_dict={test_prop.id: 24})
        with warnings.catch_warnings(record=True) as w:
            for filter_type in self.filter_types:
                prefilter = PropertyValueFilter(
                    property_model=test_prop, value=filter_value, filter_type=filter_type
                )
                widget = self.wm.add_filteredgrid_widget(
                    title=filter_type,
                    part_model=self.new_part,
                    readable_models=list(),
                    writable_models=[test_prop],
                    custom_height=300,
                    parent_instance=self.bike_instance,
                    prefilters=[prefilter],
                )
                self.assertEqual(
                    widget.meta.get("prefilters").get("property_value"),
                    f"{test_prop.id}:{filter_value}:{filter_type}",
                )
            self.assertEqual(len(w), 3)

    def test_float_property_filter_in_grid(self):
        filter_value = 22.55
        test_prop = self.new_part.add_property(
            name=self.prop_test_name, property_type=PropertyType.FLOAT_VALUE
        )
        self.bike_instance.add_with_properties(
            model=self.new_part, update_dict={test_prop.id: 15.5}
        )
        self.bike_instance.add_with_properties(
            model=self.new_part, update_dict={test_prop.id: 24.4}
        )
        with warnings.catch_warnings(record=True) as w:
            for filter_type in self.filter_types:
                prefilter = PropertyValueFilter(
                    property_model=test_prop, value=filter_value, filter_type=filter_type
                )
                widget = self.wm.add_filteredgrid_widget(
                    title=filter_type,
                    part_model=self.new_part,
                    readable_models=list(),
                    writable_models=[test_prop],
                    custom_height=300,
                    parent_instance=self.bike_instance,
                    prefilters=[prefilter],
                )
                self.assertEqual(
                    widget.meta.get("prefilters").get("property_value"),
                    f"{test_prop.id}:{filter_value}:{filter_type}",
                )
            self.assertEqual(len(w), 3)

    def test_boolean_property_filter_in_grid(self):
        filter_value = True
        test_prop = self.new_part.add_property(
            name=self.prop_test_name, property_type=PropertyType.BOOLEAN_VALUE
        )
        self.bike_instance.add_with_properties(
            model=self.new_part, update_dict={test_prop.id: False}
        )
        self.bike_instance.add_with_properties(
            model=self.new_part, update_dict={test_prop.id: True}
        )
        with warnings.catch_warnings(record=True) as w:
            for filter_type in self.filter_types:
                prefilter = PropertyValueFilter(
                    property_model=test_prop, value=filter_value, filter_type=filter_type
                )
                widget = self.wm.add_filteredgrid_widget(
                    title=filter_type,
                    part_model=self.new_part,
                    readable_models=list(),
                    writable_models=[test_prop],
                    custom_height=300,
                    parent_instance=self.bike_instance,
                    prefilters=[prefilter],
                )
                self.assertEqual(
                    widget.meta.get("prefilters").get("property_value"),
                    "{}:{}:{}".format(test_prop.id, str(filter_value).lower(), filter_type),
                )
            self.assertEqual(len(w), 4)

    def test_date_property_filter_in_grid(self):
        filter_value = str(datetime.date(2021, 5, 4))
        test_prop = self.new_part.add_property(
            name=self.prop_test_name, property_type=PropertyType.DATE_VALUE
        )
        self.bike_instance.add_with_properties(
            model=self.new_part, update_dict={test_prop.id: str(datetime.date(2021, 5, 2))}
        )
        self.bike_instance.add_with_properties(
            model=self.new_part, update_dict={test_prop.id: str(datetime.date(2021, 5, 8))}
        )
        with warnings.catch_warnings(record=True) as w:
            for filter_type in self.filter_types:
                prefilter = PropertyValueFilter(
                    property_model=test_prop, value=filter_value, filter_type=filter_type
                )
                widget = self.wm.add_filteredgrid_widget(
                    title=filter_type,
                    part_model=self.new_part,
                    readable_models=list(),
                    writable_models=[test_prop],
                    custom_height=300,
                    parent_instance=self.bike_instance,
                    prefilters=[prefilter],
                )
                self.assertEqual(
                    widget.meta.get("prefilters").get("property_value"),
                    "{}:{}:{}".format(test_prop.id, filter_value, filter_type),
                )
            self.assertEqual(len(w), 3)

    def test_link_property_filter_in_grid(self):
        filter_value = "nl"
        test_prop = self.new_part.add_property(
            name=self.prop_test_name, property_type=PropertyType.LINK_VALUE
        )
        self.bike_instance.add_with_properties(
            model=self.new_part, update_dict={test_prop.id: "https://ke-chain.com"}
        )
        self.bike_instance.add_with_properties(
            model=self.new_part, update_dict={test_prop.id: "https://ke-chain.nl"}
        )
        with warnings.catch_warnings(record=True) as w:
            for filter_type in self.filter_types:
                prefilter = PropertyValueFilter(
                    property_model=test_prop, value=filter_value, filter_type=filter_type
                )
                widget = self.wm.add_filteredgrid_widget(
                    title=filter_type,
                    part_model=self.new_part,
                    readable_models=list(),
                    writable_models=[test_prop],
                    custom_height=300,
                    parent_instance=self.bike_instance,
                    prefilters=[prefilter],
                )
                self.assertEqual(
                    widget.meta.get("prefilters").get("property_value"),
                    "{}:{}:{}".format(test_prop.id, filter_value, filter_type),
                )
            self.assertEqual(len(w), 4)

    def test_single_select_property_filter_in_grid(self):
        filter_value = "apples"
        test_prop = self.new_part.add_property(
            name=self.prop_test_name,
            options=dict(value_choices=["apples", "oranges", "bananas", "lemons"]),
            property_type=PropertyType.SINGLE_SELECT_VALUE,
        )
        self.bike_instance.add_with_properties(
            model=self.new_part, update_dict={test_prop.id: "apples"}
        )
        self.bike_instance.add_with_properties(
            model=self.new_part, update_dict={test_prop.id: "bananas"}
        )
        with warnings.catch_warnings(record=True) as w:
            for filter_type in self.filter_types:
                prefilter = PropertyValueFilter(
                    property_model=test_prop, value=filter_value, filter_type=filter_type
                )
                widget = self.wm.add_filteredgrid_widget(
                    title=filter_type,
                    part_model=self.new_part,
                    readable_models=list(),
                    writable_models=[test_prop],
                    custom_height=300,
                    parent_instance=self.bike_instance,
                    prefilters=[prefilter],
                )
                self.assertEqual(
                    widget.meta.get("prefilters").get("property_value"),
                    "{}:{}:{}".format(test_prop.id, filter_value, filter_type),
                )
            self.assertEqual(len(w), 4)

    def test_multi_select_property_filter_in_grid(self):
        filter_value = "apples"
        test_prop = self.new_part.add_property(
            name=self.prop_test_name,
            options=dict(value_choices=["apples", "oranges", "bananas", "lemons"]),
            property_type=PropertyType.MULTI_SELECT_VALUE,
        )
        self.bike_instance.add_with_properties(
            model=self.new_part, update_dict={test_prop.id: ["apples", "bananas"]}
        )
        self.bike_instance.add_with_properties(
            model=self.new_part, update_dict={test_prop.id: ["bananas", "lemons"]}
        )
        with warnings.catch_warnings(record=True) as w:
            for filter_type in self.filter_types:
                prefilter = PropertyValueFilter(
                    property_model=test_prop, value=filter_value, filter_type=filter_type
                )
                widget = self.wm.add_filteredgrid_widget(
                    title=filter_type,
                    part_model=self.new_part,
                    readable_models=list(),
                    writable_models=[test_prop],
                    custom_height=300,
                    parent_instance=self.bike_instance,
                    prefilters=[prefilter],
                )
                self.assertEqual(
                    widget.meta.get("prefilters").get("property_value"),
                    "{}:{}:{}".format(test_prop.id, filter_value, filter_type),
                )
            self.assertEqual(len(w), 4)

    def test_part_reference_property_filter_in_grid(self):
        filter_value = "Rear Wheel"
        test_prop = self.new_part.add_property(
            name=self.prop_test_name,
            default_value=self.wheel,
            property_type=PropertyType.REFERENCES_VALUE,
        )
        self.bike_instance.add_with_properties(
            model=self.new_part,
            update_dict={test_prop.id: [self.project.part(name="Front Wheel")]},
        )
        self.bike_instance.add_with_properties(
            model=self.new_part,
            update_dict={
                test_prop.id: [
                    self.project.part(name="Front Wheel"),
                    self.project.part(name="Rear Wheel"),
                ]
            },
        )
        with warnings.catch_warnings(record=True) as w:
            for filter_type in self.filter_types:
                prefilter = PropertyValueFilter(
                    property_model=test_prop, value=filter_value, filter_type=filter_type
                )
                widget = self.wm.add_filteredgrid_widget(
                    title=filter_type,
                    part_model=self.new_part,
                    readable_models=list(),
                    writable_models=[test_prop],
                    custom_height=300,
                    parent_instance=self.bike_instance,
                    prefilters=[prefilter],
                )
                self.assertEqual(
                    widget.meta.get("prefilters").get("property_value"),
                    "{}:{}:{}".format(test_prop.id, urllib.parse.quote(filter_value), filter_type),
                )
            self.assertEqual(len(w), 4)

    def test_part_reference_property_filter_in_grid_with_commas(self):
        filter_value = self.new_wheel.name
        test_prop = self.new_part.add_property(
            name=self.prop_test_name,
            default_value=self.wheel,
            property_type=PropertyType.REFERENCES_VALUE,
        )
        self.bike_instance.add_with_properties(
            model=self.new_part,
            update_dict={test_prop.id: [self.project.part(name="Front Wheel")]},
        )
        self.bike_instance.add_with_properties(
            model=self.new_part,
            update_dict={
                test_prop.id: [
                    self.project.part(name="Front Wheel"),
                    self.project.part(name="Rear Wheel"),
                ]
            },
        )
        with warnings.catch_warnings(record=True) as w:
            for filter_type in self.filter_types:
                prefilter = PropertyValueFilter(
                    property_model=test_prop, value=filter_value, filter_type=filter_type
                )
                widget = self.wm.add_filteredgrid_widget(
                    title=filter_type,
                    part_model=self.new_part,
                    readable_models=list(),
                    writable_models=[test_prop],
                    custom_height=300,
                    parent_instance=self.bike_instance,
                    prefilters=[prefilter],
                )
                self.assertEqual(
                    widget.meta.get("prefilters").get("property_value"),
                    "{}:{}:{}".format(test_prop.id, urllib.parse.quote(filter_value), filter_type),
                )
            self.assertEqual(len(w), 4)

    def test_activity_reference_property_filter_in_grid(self):
        filter_value = "Specify wheel diameter"
        test_prop = self.new_part.add_property(
            name=self.prop_test_name, property_type=PropertyType.ACTIVITY_REFERENCES_VALUE
        )
        self.bike_instance.add_with_properties(
            model=self.new_part,
            update_dict={test_prop.id: [self.project.activity(name="Subprocess")]},
        )
        self.bike_instance.add_with_properties(
            model=self.new_part,
            update_dict={
                test_prop.id: [
                    self.project.activity(name="Specify wheel diameter"),
                    self.project.activity(name="Subprocess"),
                ]
            },
        )
        with warnings.catch_warnings(record=True) as w:
            for filter_type in self.filter_types:
                prefilter = PropertyValueFilter(
                    property_model=test_prop, value=filter_value, filter_type=filter_type
                )
                widget = self.wm.add_filteredgrid_widget(
                    title=filter_type,
                    part_model=self.new_part,
                    readable_models=list(),
                    writable_models=[test_prop],
                    custom_height=300,
                    parent_instance=self.bike_instance,
                    prefilters=[prefilter],
                )
                self.assertEqual(
                    widget.meta.get("prefilters").get("property_value"),
                    "{}:{}:{}".format(test_prop.id, urllib.parse.quote(filter_value), filter_type),
                )
            self.assertEqual(len(w), 4)

    def test_user_reference_property_filter_in_grid(self):
        filter_value = "Test"
        test_prop = self.new_part.add_property(
            name=self.prop_test_name, property_type=PropertyType.USER_REFERENCES_VALUE
        )
        self.bike_instance.add_with_properties(
            model=self.new_part,
            update_dict={test_prop.id: [self.client.user(username="superuser")]},
        )
        self.bike_instance.add_with_properties(
            model=self.new_part,
            update_dict={
                test_prop.id: [
                    self.client.user(username="testuser"),
                    self.client.user(username="superuser"),
                ]
            },
        )
        with warnings.catch_warnings(record=True) as w:
            for filter_type in self.filter_types:
                prefilter = PropertyValueFilter(
                    property_model=test_prop, value=filter_value, filter_type=filter_type
                )
                widget = self.wm.add_filteredgrid_widget(
                    title=filter_type,
                    part_model=self.new_part,
                    readable_models=list(),
                    writable_models=[test_prop],
                    custom_height=300,
                    parent_instance=self.bike_instance,
                    prefilters=[prefilter],
                )
                self.assertEqual(
                    widget.meta.get("prefilters").get("property_value"),
                    "{}:{}:{}".format(test_prop.id, filter_value, filter_type),
                )
            self.assertEqual(len(w), 4)

    def test_scope_reference_property_filter_in_grid(self):
        filter_value = "Bike"
        test_prop = self.new_part.add_property(
            name=self.prop_test_name, property_type=PropertyType.SCOPE_REFERENCES_VALUE
        )
        self.bike_instance.add_with_properties(
            model=self.new_part,
            update_dict={test_prop.id: [self.client.scope("Cannondale Project")]},
        )
        self.bike_instance.add_with_properties(
            model=self.new_part,
            update_dict={
                test_prop.id: [
                    self.client.scope("Cannondale Project"),
                    self.client.scope("Bike Project"),
                ]
            },
        )
        with warnings.catch_warnings(record=True) as w:
            for filter_type in self.filter_types:
                prefilter = PropertyValueFilter(
                    property_model=test_prop, value=filter_value, filter_type=filter_type
                )
                widget = self.wm.add_filteredgrid_widget(
                    title=filter_type,
                    part_model=self.new_part,
                    readable_models=list(),
                    writable_models=[test_prop],
                    custom_height=300,
                    parent_instance=self.bike_instance,
                    prefilters=[prefilter],
                )
                self.assertEqual(
                    widget.meta.get("prefilters").get("property_value"),
                    "{}:{}:{}".format(test_prop.id, filter_value, filter_type),
                )
            self.assertEqual(len(w), 4)

    def test_part_reference_property_prefilter(self):
        filter_type = FilterType.GREATER_THAN_EQUAL
        filter_value = 4.2
        filter_property_model = self.wheel.property("Tire Thickness")
        test_prop = self.new_part.add_property(
            name=self.prop_test_name,
            default_value=self.wheel,
            property_type=PropertyType.REFERENCES_VALUE,
        )
        prefilter = PropertyValueFilter(
            property_model=filter_property_model, value=filter_value, filter_type=filter_type
        )
        test_prop.set_prefilters(prefilters=[prefilter])
        self.assertEqual(
            test_prop._options.get("prefilters").get("property_value"),
            f"{filter_property_model.id}:{filter_value}:{filter_type}",
        )

    def test_activity_reference_property_prefilter(self):
        test_prop = self.new_part.add_property(
            name=self.prop_test_name, property_type=PropertyType.SCOPE_REFERENCES_VALUE
        )
        prefilters = [
            ScopeFilter(tag="bike"),
            ScopeFilter(tag="bmx"),
            ScopeFilter(progress_gte=1.0),
        ]
        test_prop.set_prefilters(prefilters=prefilters)
        self.assertEqual(test_prop._options.get("prefilters").get("tags__contains"), "bike,bmx")
        self.assertEqual(test_prop._options.get("prefilters").get("progress__gte"), 1.0)


class BaseTest:
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
                raise ValueError(f"Test needs 2 different values ({cls.VALUE}, {cls.VALUE_2})")

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

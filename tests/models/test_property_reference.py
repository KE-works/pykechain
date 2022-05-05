from unittest import TestCase, skip

from pykechain.enums import (
    ActivityRootNames,
    ContextGroup,
    ContextType,
    FilterType,
    FormCategory,
    Multiplicity,
    PropertyType,
    StatusCategory,
    WorkflowCategory,
)
from pykechain.exceptions import ForbiddenError, IllegalArgumentError, NotFoundError
from pykechain.models import MultiReferenceProperty
from pykechain.models.base_reference import _ReferenceProperty
from pykechain.models.property_reference import (
    ActivityReferencesProperty,
    ContextReferencesProperty,
    FormReferencesProperty,
    ScopeReferencesProperty,
    StatusReferencesProperty,
    UserReferencesProperty,
)
from pykechain.models.validators import RequiredFieldValidator
from pykechain.models.value_filter import PropertyValueFilter, ScopeFilter
from pykechain.models.workflow import Status, Workflow
from pykechain.utils import find, is_uuid
from tests.classes import TestBetamax


class TestPropertyBaseReference(TestCase):
    def setUp(self) -> None:
        super().setUp()
        self.base_ref = _ReferenceProperty(json=dict(), client=None)

    def test_prefilters(self):
        with self.assertRaises(NotImplementedError):
            self.base_ref.set_prefilters()

        with self.assertRaises(NotImplementedError):
            self.base_ref.get_prefilters()


class TestPropertyMultiReferenceProperty(TestBetamax):
    def setUp(self):
        super().setUp()

        # reference Part target (model and 1 instance)
        _wheel_model = self.project.model(ref="wheel")

        props = [
            PropertyType.DATETIME_VALUE,
            PropertyType.SINGLE_SELECT_VALUE,
            PropertyType.BOOLEAN_VALUE,
            PropertyType.FLOAT_VALUE,
            PropertyType.INT_VALUE,
            PropertyType.CHAR_VALUE,
        ]

        self.target_model = self.project.create_model_with_properties(
            parent=_wheel_model.parent_id,
            name="__Wheel",
            multiplicity=Multiplicity.ONE_MANY,
            properties_fvalues=[dict(name=p, property_type=p) for p in props],
        )

        # reference property model (with a value pointing to a reference target part model
        self.part_model = self.project.model("Bike")

        self.datetime_prop = self.target_model.property(PropertyType.DATETIME_VALUE)
        self.ssl_prop = self.target_model.property(PropertyType.SINGLE_SELECT_VALUE)
        self.bool_prop = self.target_model.property(PropertyType.BOOLEAN_VALUE)
        self.float_prop = self.target_model.property(PropertyType.FLOAT_VALUE)
        self.integer_prop = self.target_model.property(PropertyType.INT_VALUE)
        self.char_prop = self.target_model.property(PropertyType.CHAR_VALUE)

        self.ref_prop_name = "__Test reference property"
        self.ref_prop_model = self.part_model.add_property(
            name=self.ref_prop_name,
            property_type=PropertyType.REFERENCES_VALUE,
            default_value=self.target_model.id,
        )  # type: MultiReferenceProperty

        # reference property instance holding the value
        part_instance = self.part_model.instance()
        self.ref = find(
            part_instance.properties, lambda p: p.model_id == self.ref_prop_model.id
        )  # type: MultiReferenceProperty

    def tearDown(self):
        self.target_model.delete()
        self.ref_prop_model.delete()
        super().tearDown()

    def test_referencing_a_model(self):
        # setUp
        wheel_model = self.project.model("Wheel")
        self.ref_prop_model.value = [wheel_model]

        # testing
        self.assertEqual(len(list(self.ref_prop_model.value)), 1)

    def test_referencing_multiple_instances_using_parts(self):
        # setUp
        wheel_model = self.project.model("Wheel")
        self.ref_prop_model.value = [wheel_model]
        wheel_instances = wheel_model.instances()
        wheel_instances_list = [instance for instance in wheel_instances]

        # set ref value
        self.ref.value = wheel_instances_list

        # testing
        self.assertTrue(len(self.ref.value) >= 2)

    def test_referencing_multiple_instances_using_ids(self):
        # setUp
        wheel_model = self.project.model("Wheel")
        self.ref_prop_model.value = [wheel_model]
        wheel_instances = wheel_model.instances()
        wheel_instances_list = [instance.id for instance in wheel_instances]

        # set ref value
        self.ref.value = wheel_instances_list
        self.ref._cached_values = None

        # testing
        self.assertTrue(len(self.ref.value) >= 2)

    def test_referencing_a_list_with_no_parts(self):
        # setUp
        fake_part = [15, 21, 26]

        # testing
        with self.assertRaises(ValueError):
            self.ref.value = fake_part

    def test_value_if_multi_ref_gives_back_all_parts(self):
        """because of #276 problem"""
        # setUp
        self.ref_prop_model.value = [self.target_model]

        wheel_instances = self.target_model.instances()
        wheel_instances_list = [instance.id for instance in wheel_instances]

        # set ref value
        self.ref.value = wheel_instances_list
        self.ref.refresh()

        # testing
        all_referred_parts = self.ref.value
        self.assertEqual(len(all_referred_parts), len(self.ref._value))

    def test_value_if_nothing_is_referenced(self):
        # setUp
        value_of_multi_ref = self.ref.value

        # testing
        self.assertFalse(self.ref.has_value())
        self.assertIsNone(value_of_multi_ref)

    def test_value_ids(self):
        wheel_instances = self.target_model.instances()
        wheel_instances_list = [instance.id for instance in wheel_instances]
        self.ref.value = wheel_instances_list
        self.ref.refresh()

        ids = self.ref.value_ids()

        self.assertIsInstance(ids, list)
        self.assertTrue(all(isinstance(v, str) for v in ids))

    def test_multi_ref_choices(self):
        # setUp
        self.project.part(ref="bike").add_with_properties(
            name="__Wheel 2",
            model=self.target_model,
            update_dict={
                PropertyType.BOOLEAN_VALUE: True,
            },
        )
        self.ref_prop_model.value = [self.target_model]
        possible_options = self.ref.choices()

        # testing
        self.assertEqual(2, len(possible_options))

        self.ref_prop_model.set_prefilters(
            property_models=[self.target_model.property(PropertyType.BOOLEAN_VALUE)],
            values=[True],
            filters_type=[FilterType.EXACT],
        )
        self.ref.refresh()

        possible_options = self.ref.choices()
        self.assertEqual(1, len(possible_options))

    def test_create_ref_property_referencing_part_in_list(self):
        # setUp
        new_reference_to_wheel = self.part_model.add_property(
            name=self.ref_prop_name,
            property_type=PropertyType.REFERENCES_VALUE,
            default_value=[self.target_model],
        )
        # testing
        self.assertTrue(self.ref_prop_model.value[0].id, self.target_model.id)

        # tearDown
        new_reference_to_wheel.delete()

    def test_create_ref_property_referencing_id_in_list(self):
        # setUp
        new_reference_to_wheel = self.part_model.add_property(
            name=self.ref_prop_name,
            property_type=PropertyType.REFERENCES_VALUE,
            default_value=[self.target_model.id],
        )
        # testing
        self.assertTrue(self.ref_prop_model.value[0].id, self.target_model.id)

        # tearDown
        new_reference_to_wheel.delete()

    def test_create_ref_property_wrongly_referencing_in_list(self):
        # testing
        with self.assertRaises(IllegalArgumentError):
            self.part_model.add_property(
                name=self.ref_prop_name,
                property_type=PropertyType.REFERENCES_VALUE,
                default_value=[12],
            )

    def test_create_ref_property_referencing_part(self):
        # setUp
        new_reference_to_wheel = self.part_model.add_property(
            name=self.ref_prop_name,
            property_type=PropertyType.REFERENCES_VALUE,
            default_value=self.target_model,
        )
        # testing
        self.assertTrue(self.ref_prop_model.value[0].id, self.target_model.id)

        # tearDown
        new_reference_to_wheel.delete()

    def test_create_ref_property_referencing_id(self):
        # setUp
        new_reference_to_wheel = self.part_model.add_property(
            name=self.ref_prop_name,
            property_type=PropertyType.REFERENCES_VALUE,
            default_value=self.target_model.id,
        )
        # testing
        self.assertTrue(self.ref_prop_model.value[0].id, self.target_model.id)

        # tearDown
        new_reference_to_wheel.delete()

    def test_create_ref_property_wrongly_referencing(self):
        # testing
        with self.assertRaises(IllegalArgumentError):
            self.part_model.add_property(
                name=self.ref_prop_name,
                property_type=PropertyType.REFERENCES_VALUE,
                default_value=True,
            )

    # new in 3.0
    def test_set_prefilters_on_reference_property(self):
        # setUp
        diameter_property = self.float_prop  # decimal property
        spokes_property = self.integer_prop  # integer property
        rim_material_property = self.char_prop  # single line text

        self.ref_prop_model.set_prefilters(
            property_models=[
                diameter_property,
                spokes_property,
                rim_material_property,
                self.datetime_prop,
                self.ssl_prop,
                self.bool_prop,
            ],
            values=[30.5, 7, "Al", self.time, "Michelin", True],
            filters_type=[
                FilterType.GREATER_THAN_EQUAL,
                FilterType.LOWER_THAN_EQUAL,
                FilterType.CONTAINS,
                FilterType.GREATER_THAN_EQUAL,
                FilterType.CONTAINS,
                FilterType.EXACT,
            ],
        )
        self.assertIn("property_value", self.ref_prop_model._options["prefilters"])

        filter_string = self.ref_prop_model._options["prefilters"]["property_value"]
        filters = set(filter_string.split(","))

        # testing
        self.assertIn(
            "{}:{}:{}".format(
                diameter_property.id, 30.5, FilterType.GREATER_THAN_EQUAL
            ),
            filters,
        )
        self.assertIn(
            f"{spokes_property.id}:{7}:{FilterType.LOWER_THAN_EQUAL}",
            filters,
        )
        self.assertIn(
            "{}:{}:{}".format(rim_material_property.id, "Al", FilterType.CONTAINS),
            filters,
        )
        self.assertIn(
            "{}:{}:{}".format(self.bool_prop.id, "true", FilterType.EXACT), filters
        )
        self.assertIn(
            "{}:{}:{}".format(self.ssl_prop.id, "Michelin", FilterType.CONTAINS),
            filters,
        )
        self.assertIn(
            "{}:{}:{}".format(
                self.datetime_prop.id, self.time, FilterType.GREATER_THAN_EQUAL
            ),
            filters,
        )

    def test_set_prefilters_with_tuples(self):
        prefilters_set = [
            PropertyValueFilter(self.float_prop, 15.3, FilterType.GREATER_THAN_EQUAL),
            PropertyValueFilter(self.char_prop, "Al", FilterType.CONTAINS),
        ]

        self.ref_prop_model.set_prefilters(prefilters=prefilters_set)

        prefilters_get = self.ref_prop_model.get_prefilters()

        self.assertTrue(prefilters_get, msg="No prefilters returned")
        first_filter = prefilters_get[0]

        self.assertEqual(self.float_prop.id, first_filter.id)
        self.assertEqual("15.3", first_filter.value)
        self.assertEqual(FilterType.GREATER_THAN_EQUAL, first_filter.type)

    def test_set_prefilters_with_validation(self):
        prefilter_good = PropertyValueFilter(
            self.float_prop, 15.3, FilterType.GREATER_THAN_EQUAL
        )
        prefilter_bad = PropertyValueFilter(
            self.part_model.property("Gears"), 15.3, FilterType.GREATER_THAN_EQUAL
        )

        # Validate automatically
        self.ref_prop_model.set_prefilters(prefilters=[prefilter_good])
        with self.assertRaises(IllegalArgumentError):
            self.ref_prop_model.set_prefilters(prefilters=[prefilter_bad])

        # Validate by providing the referenced model
        self.ref_prop_model.set_prefilters(
            prefilters=[prefilter_good], validate=self.target_model
        )
        with self.assertRaises(IllegalArgumentError):
            self.ref_prop_model.set_prefilters(
                prefilters=[prefilter_bad], validate=self.target_model
            )

        # Dont validate
        self.ref_prop_model.set_prefilters(prefilters=[prefilter_good], validate=False)
        self.ref_prop_model.set_prefilters(prefilters=[prefilter_bad], validate=None)

    def test_set_prefilters_on_reference_property_with_excluded_propmodels_and_validators(
        self,
    ):
        # The excluded propmodels and validators already set on the property should not be erased when
        # setting prefilters

        # setUp
        diameter_property = self.float_prop
        spokes_property = self.integer_prop

        self.ref_prop_model.set_excluded_propmodels(
            property_models=[diameter_property, spokes_property]
        )
        self.ref_prop_model.validators = [RequiredFieldValidator()]

        self.ref_prop_model.set_prefilters(
            property_models=[diameter_property],
            values=[15.13],
            filters_type=[FilterType.GREATER_THAN_EQUAL],
        )

        # testing Filters
        self.assertIn(
            "{}:{}:{}".format(
                diameter_property.id, 15.13, FilterType.GREATER_THAN_EQUAL
            ),
            self.ref_prop_model._options["prefilters"]["property_value"],
        )

        # testing Excluded props
        self.assertIn("propmodels_excl", self.ref_prop_model._options)
        excluded = self.ref_prop_model._options["propmodels_excl"]

        self.assertEqual(len(excluded), 2)
        self.assertIn(diameter_property.id, excluded)
        self.assertIn(spokes_property.id, excluded)

        # testing Validators
        self.assertTrue(self.ref_prop_model.validators)
        self.assertIsInstance(
            self.ref_prop_model._validators[0], RequiredFieldValidator
        )

    def test_clear_prefilters(self):
        # setUp
        prefilter_1 = PropertyValueFilter(
            property_model=self.float_prop,
            value=15.13,
            filter_type=FilterType.GREATER_THAN_EQUAL,
        )
        self.ref_prop_model.set_prefilters(prefilters=[prefilter_1])

        # Add filter for different property, see if the first one is removed (clear = True)
        prefilter_2 = PropertyValueFilter(
            property_model=self.integer_prop,
            value=13,
            filter_type=FilterType.EXACT,
        )
        self.ref_prop_model.set_prefilters(
            prefilters=[prefilter_2],
            clear=True,
        )

        self.ref_prop_model.refresh()
        live_prefilters = self.ref_prop_model.get_prefilters()

        # testing
        self.assertTrue(live_prefilters, msg="Expected at least 1 prefilter")
        self.assertEqual(1, len(live_prefilters), msg="Expected 1 prefilter")
        self.assertEqual(prefilter_2, live_prefilters[0])

    def test_overwrite_prefilters(self):
        # setUp
        prefilter_1 = PropertyValueFilter(
            property_model=self.float_prop,
            value=15.13,
            filter_type=FilterType.GREATER_THAN_EQUAL,
        )
        prefilter_2 = PropertyValueFilter(
            property_model=self.integer_prop,
            value=13,
            filter_type=FilterType.EXACT,
        )
        prefilter_3 = PropertyValueFilter(
            property_model=self.float_prop,
            value=15.13,
            filter_type=FilterType.EXACT,
        )
        # Set the initial filters
        self.ref_prop_model.set_prefilters(prefilters=[prefilter_1, prefilter_2])

        # Add another filter for the same property to see if the first one is removed (overwrite = True)
        self.ref_prop_model.set_prefilters(prefilters=[prefilter_3], overwrite=True)

        self.ref_prop_model.refresh()
        live_prefilters = self.ref_prop_model.get_prefilters()

        # testing
        self.assertTrue(live_prefilters, msg="Expected at least 1 prefilter")
        self.assertEqual(2, len(live_prefilters), msg="Expected 2 prefilters")
        self.assertIn(prefilter_2, live_prefilters)
        self.assertIn(prefilter_3, live_prefilters)

    def test_set_prefilters_on_reference_property_using_uuid(self):
        # setUp
        diameter_property = self.float_prop
        spokes_property = self.integer_prop

        self.ref_prop_model.set_prefilters(
            property_models=[diameter_property.id, spokes_property.id],
            values=[30.5, 7],
            filters_type=[FilterType.GREATER_THAN_EQUAL, FilterType.LOWER_THAN_EQUAL],
        )

        # testing
        self.assertTrue("property_value" in self.ref_prop_model._options["prefilters"])
        self.assertTrue(
            f"{diameter_property.id}:{30.5}:{FilterType.GREATER_THAN_EQUAL}"
            in self.ref_prop_model._options["prefilters"]["property_value"]
        )
        self.assertTrue(
            f"{spokes_property.id}:{7}:{FilterType.LOWER_THAN_EQUAL}"
            in self.ref_prop_model._options["prefilters"]["property_value"]
        )

    def test_set_prefilters_on_reference_property_the_wrong_way(self):
        # setUp
        bike_gears_property = self.part_model.property(name="Gears")
        instance_diameter_property = self.target_model.instances()[0].property(
            PropertyType.FLOAT_VALUE
        )
        diameter_property = self.float_prop

        # testing
        # When prefilters are being set, but the property does not belong to the referenced part
        with self.assertRaises(IllegalArgumentError):
            self.ref_prop_model.set_prefilters(
                property_models=[bike_gears_property],
                values=[2],
                filters_type=[FilterType.GREATER_THAN_EQUAL],
            )

        # When prefilters are being set, but the property is an instance, not a model
        with self.assertRaises(IllegalArgumentError):
            self.ref_prop_model.set_prefilters(
                property_models=[instance_diameter_property],
                values=[3.33],
                filters_type=[FilterType.GREATER_THAN_EQUAL],
            )

        # When prefilters are being set, but the size of lists is not consistent
        with self.assertRaises(IllegalArgumentError):
            self.ref_prop_model.set_prefilters(
                property_models=[diameter_property],
                values=[3.33, 1.51],
                filters_type=[FilterType.GREATER_THAN_EQUAL, FilterType.CONTAINS],
            )

        # When prefilters are being set, but no UUIDs or `Property` objects are being used in property_models
        with self.assertRaises(IllegalArgumentError):
            # noinspection PyTypeChecker
            self.ref_prop_model.set_prefilters(
                property_models=[False, 301],
                values=[3.33, 1.51],
                filters_type=[FilterType.GREATER_THAN_EQUAL, FilterType.CONTAINS],
            )

    def test_set_excluded_propmodels_on_reference_property(self):
        # setUp
        diameter_property = self.float_prop
        spokes_property = self.integer_prop

        self.ref_prop_model.set_excluded_propmodels(
            property_models=[diameter_property, spokes_property]
        )

        # testing
        self.assertEqual(len(self.ref_prop_model._options["propmodels_excl"]), 2)
        self.assertTrue(
            diameter_property.id in self.ref_prop_model._options["propmodels_excl"]
        )
        self.assertTrue(
            spokes_property.id in self.ref_prop_model._options["propmodels_excl"]
        )

    def test_set_excluded_propmodels_with_validation(self):
        excluded_model_good = self.float_prop
        excluded_model_bad = self.part_model.property("Gears")

        # Validate automatically
        self.ref_prop_model.set_excluded_propmodels(
            property_models=[excluded_model_good]
        )
        with self.assertRaises(IllegalArgumentError):
            self.ref_prop_model.set_excluded_propmodels(
                property_models=[excluded_model_bad]
            )

        # Validate by providing the referenced model
        self.ref_prop_model.set_excluded_propmodels(
            property_models=[excluded_model_good], validate=self.target_model
        )
        with self.assertRaises(IllegalArgumentError):
            self.ref_prop_model.set_excluded_propmodels(
                property_models=[excluded_model_bad], validate=self.target_model
            )

        # Dont validate
        self.ref_prop_model.set_excluded_propmodels(
            property_models=[excluded_model_good], validate=False
        )
        self.ref_prop_model.set_excluded_propmodels(
            property_models=[excluded_model_bad], validate=None
        )

    def test_set_excluded_propmodels_on_reference_property_using_uuid(self):
        # setUp
        diameter_property = self.float_prop
        spokes_property = self.integer_prop

        self.ref_prop_model.set_excluded_propmodels(
            property_models=[diameter_property.id, spokes_property.id]
        )

        # testing
        self.assertEqual(len(self.ref_prop_model._options["propmodels_excl"]), 2)
        self.assertTrue(
            diameter_property.id in self.ref_prop_model._options["propmodels_excl"]
        )
        self.assertTrue(
            spokes_property.id in self.ref_prop_model._options["propmodels_excl"]
        )

    def test_set_excluded_propmodels_on_reference_property_with_prefilters_and_validators(
        self,
    ):
        # The prefilters and validators already set on the property should not be erased when setting
        # excluded propmodels

        # setUp
        diameter_property = self.float_prop
        spokes_property = self.integer_prop
        self.ref_prop_model.set_prefilters(
            property_models=[diameter_property],
            values=[15.13],
            filters_type=[FilterType.GREATER_THAN_EQUAL],
        )

        self.ref_prop_model.validators = [RequiredFieldValidator()]

        self.ref_prop_model.set_excluded_propmodels(
            property_models=[diameter_property, spokes_property]
        )

        # testing
        self.assertTrue("property_value" in self.ref_prop_model._options["prefilters"])
        self.assertTrue(
            "{}:{}:{}".format(
                diameter_property.id, 15.13, FilterType.GREATER_THAN_EQUAL
            )
            in self.ref_prop_model._options["prefilters"]["property_value"]
        )
        self.assertEqual(len(self.ref_prop_model._options["propmodels_excl"]), 2)
        self.assertTrue(
            diameter_property.id in self.ref_prop_model._options["propmodels_excl"]
        )
        self.assertTrue(
            spokes_property.id in self.ref_prop_model._options["propmodels_excl"]
        )
        self.assertTrue(
            isinstance(self.ref_prop_model._validators[0], RequiredFieldValidator)
        )

    def test_get_prefilters(self):
        # setUp
        self.ref_prop_model.set_prefilters(
            property_models=[self.float_prop],
            values=[15.13],
            filters_type=[FilterType.GREATER_THAN_EQUAL],
        )

        prefilters = self.ref_prop_model.get_prefilters()

        self.assertTrue(prefilters, msg="A prefilter should be set")

        self.assertIsInstance(
            prefilters, list, msg="By default, prefilters should be a list of tuples!"
        )
        self.assertTrue(
            all(isinstance(pf, PropertyValueFilter) for pf in prefilters),
            msg="Not every prefilter is a PropertyValueFilter object!",
        )

        prefilters = self.ref_prop_model.get_prefilters(as_lists=True)

        self.assertIsInstance(
            prefilters, tuple, msg="Prefilters should be a tuple of 3 lists!"
        )
        self.assertEqual(3, len(prefilters), msg="Expected 3 lists!")

        property_model_ids, values, filters = prefilters

        self.assertEqual(len(property_model_ids), len(values), len(filters))

    def test_set_excluded_propmodels_on_reference_property_the_wrong_way(self):
        # setUp
        bike_gears_property = self.part_model.property(name="Gears")
        instance_diameter_property = self.target_model.instances()[0].property(
            PropertyType.FLOAT_VALUE
        )

        # testing
        # When excluded propmodels are being set, but the property does not belong to the referenced part
        with self.assertRaises(IllegalArgumentError):
            self.ref_prop_model.set_excluded_propmodels(
                property_models=[bike_gears_property]
            )

        # When excluded propmodels are being set, but the property is an instance, not a model
        with self.assertRaises(IllegalArgumentError):
            self.ref_prop_model.set_excluded_propmodels(
                property_models=[instance_diameter_property]
            )

        # When excluded propmodels are being set, but no UUIDs or `Property` objects are being used in property_models
        with self.assertRaises(IllegalArgumentError):
            # noinspection PyTypeChecker
            self.ref_prop_model.set_excluded_propmodels(property_models=[False, 301])

    def test_add_excluded_propmodels_to_reference_property(self):
        # Set the initial excluded propmodels
        self.ref_prop_model.set_excluded_propmodels(property_models=[self.float_prop])

        # Add others, checks whether the initial ones are remembered (overwrite = False)
        self.ref_prop_model.set_excluded_propmodels(
            property_models=[self.integer_prop], overwrite=False
        )

        # testing
        self.assertEqual(len(self.ref_prop_model._options["propmodels_excl"]), 2)
        self.assertTrue(
            self.float_prop.id in self.ref_prop_model._options["propmodels_excl"]
        )
        self.assertTrue(
            self.integer_prop.id in self.ref_prop_model._options["propmodels_excl"]
        )

    def test_overwrite_excluded_propmodels_on_reference_property(self):
        # setUp
        diameter_property = self.float_prop
        spokes_property = self.integer_prop

        # Set the initial excluded propmodels
        self.ref_prop_model.set_excluded_propmodels(property_models=[diameter_property])

        # Overwrite them
        self.ref_prop_model.set_excluded_propmodels(
            property_models=[spokes_property], overwrite=True
        )

        # testing
        self.assertEqual(len(self.ref_prop_model._options["propmodels_excl"]), 1)
        self.assertTrue(
            diameter_property.id not in self.ref_prop_model._options["propmodels_excl"]
        )
        self.assertTrue(
            spokes_property.id in self.ref_prop_model._options["propmodels_excl"]
        )

    def test_get_excluded_propmodel_ids(self):
        # setUp
        self.ref_prop_model.set_excluded_propmodels(property_models=[self.float_prop])

        excluded_propmodel_ids = self.ref_prop_model.get_excluded_propmodel_ids()

        self.assertTrue(excluded_propmodel_ids, msg="Excluded propmodels should be set")
        self.assertIsInstance(excluded_propmodel_ids, list)
        self.assertTrue(all(is_uuid(pk) for pk in excluded_propmodel_ids))

    def test_retrieve_scope_id(self):
        frame = self.project.part(name="Frame")

        ref_to_wheel = frame.property(name="Ref to wheel")

        self.assertEqual(ref_to_wheel.scope_id, self.project.id)

    def test_property_clear_selected_part_model(self):
        # setUp
        wheel_model = self.project.model("Wheel")
        self.ref_prop_model.value = [wheel_model]

        self.assertTrue(wheel_model.id == self.ref_prop_model.value[0].id)

        self.ref_prop_model.value = None

        # testing
        self.assertIsNone(self.ref_prop_model.value)

    def test_property_clear_referenced_part_instances(self):
        # setUp
        wheel_model = self.project.model("Wheel")
        self.ref_prop_model.value = [wheel_model]

        wheel_instances = wheel_model.instances()
        wheel_instances_list = [instance.id for instance in wheel_instances]

        # set ref value
        self.ref.value = wheel_instances_list

        # clear referenced part instances
        self.ref.value = None

        # testing
        self.assertIsNone(self.ref.value)
        self.assertIsNotNone(self.ref_prop_model.value)

    def test_copy_reference_property_with_options(self):
        # setUp
        copied_ref_property = self.ref_prop_model.copy(
            target_part=self.part_model, name="__Copied ref property"
        )

        # testing
        self.assertEqual(copied_ref_property.name, "__Copied ref property")
        self.assertEqual(
            copied_ref_property.description, self.ref_prop_model.description
        )
        self.assertEqual(copied_ref_property.unit, self.ref_prop_model.unit)
        self.assertEqual(copied_ref_property.value, self.ref_prop_model.value)
        self.assertDictEqual(copied_ref_property._options, self.ref_prop_model._options)

        # tearDown
        copied_ref_property.delete()


class TestPropertyMultiReferencePropertyXScope(TestBetamax):
    def setUp(self):
        super().setUp()
        self.x_scope = self.client.create_scope(
            name="Cross_reference scope", tags=["x-scope-target"]
        )

        self.part_model = self.project.model("Bike")

        # Create reference property and retrieve its instance
        prop_name = "cross-scope reference property"
        self.x_reference_model = self.part_model.add_property(
            name=prop_name,
            property_type=PropertyType.REFERENCES_VALUE,
        )
        self.x_reference = self.part_model.instance().property(prop_name)

        # Define target model and create an instance
        product_root = self.x_scope.model("Product")
        self.x_target_model = product_root.add_model(
            name="Reference target", multiplicity=Multiplicity.ZERO_MANY
        )
        self.x_target = product_root.instance().add(
            model=self.x_target_model, name="Target instance"
        )

    def tearDown(self):
        self.x_reference_model.delete()
        self.x_scope.delete()
        super().tearDown()

    def test_set_model_value(self):
        # setUp
        self.x_reference_model.value = [self.x_target_model]
        self.x_reference_model.refresh()

        # testing
        self.assertEqual(self.x_scope.id, self.x_reference_model.value[0].scope_id)
        self.assertEqual(self.x_target_model.id, self.x_reference_model.value[0].id)

    def test_set_model_value_using_id(self):
        # setUp
        self.x_reference_model.value = [self.x_target_model.id]
        self.x_reference_model.refresh()

        # testing
        self.assertEqual(self.x_scope.id, self.x_reference_model.value[0].scope_id)
        self.assertEqual(self.x_target_model.id, self.x_reference_model.value[0].id)

    def test_set_value(self):
        # setUp
        self.x_reference_model.value = [self.x_target_model.id]
        self.x_reference.refresh()
        self.x_reference.value = [self.x_target]

        self.assertTrue(len(self.x_reference.value) == 1)
        self.assertEqual(self.x_target.id, self.x_reference.value[0].id)


class TestPropertyActivityReference(TestBetamax):
    def setUp(self):
        super().setUp()
        root = self.project.model(name="Product")
        self.part = self.project.create_model(
            name="The part", parent=root, multiplicity=Multiplicity.ONE
        )
        self.prop = self.part.add_property(
            name="activity ref", property_type=PropertyType.ACTIVITY_REFERENCES_VALUE
        )

    def tearDown(self):
        if self.part:
            self.part.delete()
        super().tearDown()

    def test_create(self):
        self.assertIsInstance(self.prop, ActivityReferencesProperty)

    def test_value(self):
        wbs_root = self.project.activity(name=ActivityRootNames.WORKFLOW_ROOT)
        task = wbs_root.children()[0]

        self.prop.value = [task]
        self.prop.refresh()

        self.assertIsInstance(self.prop, ActivityReferencesProperty)
        self.assertIsNotNone(self.prop.value)
        self.assertEqual(task, self.prop.value[0])

    def test_value_ids(self):
        wbs_root = self.project.activity(name=ActivityRootNames.WORKFLOW_ROOT)
        task = wbs_root.children()[0]

        self.prop.value = [task]
        self.prop.refresh()

        ids = self.prop.value_ids()

        self.assertIsInstance(ids, list)
        self.assertTrue(all(isinstance(v, str) for v in ids))

    def test_reload(self):
        reloaded_prop = self.client.reload(obj=self.prop)

        self.assertFalse(
            self.prop is reloaded_prop,
            msg="Must be different Python objects, based on memory allocation",
        )
        self.assertEqual(
            self.prop,
            reloaded_prop,
            msg="Must be the same KE-chain prop, based on hashed UUID",
        )


class TestPropertyScopeReference(TestBetamax):
    def setUp(self):
        super().setUp()
        root = self.project.model(name="Product")

        self.part = self.project.create_model(
            name="Test part", parent=root, multiplicity=Multiplicity.ONE
        )
        self.scope_ref_prop = self.part.add_property(
            name="scope ref", property_type=PropertyType.SCOPE_REFERENCES_VALUE
        )  # type: ScopeReferencesProperty

    def tearDown(self):
        if self.part:
            self.part.delete()
        super().tearDown()

    def test_create(self):
        self.assertIsInstance(self.scope_ref_prop, ScopeReferencesProperty)

    def test_value(self):
        bike_project = self.client.scope(name="Bike Project")

        self.scope_ref_prop.value = [bike_project]

        self.assertIsInstance(self.scope_ref_prop, ScopeReferencesProperty)
        self.assertIsNotNone(self.scope_ref_prop.value)
        self.assertEqual(bike_project, self.scope_ref_prop.value[0])

    def test_value_ids(self):
        bike_project = self.client.scope(name="Bike Project")

        self.scope_ref_prop.value = [bike_project]
        self.scope_ref_prop.refresh()

        ids = self.scope_ref_prop.value_ids()

        self.assertIsInstance(ids, list)
        self.assertTrue(all(isinstance(v, str) for v in ids))

    def test_no_value(self):
        self.assertIsInstance(self.scope_ref_prop, ScopeReferencesProperty)
        self.assertIsNone(self.scope_ref_prop.value)

    def test_reload(self):
        reloaded_prop = self.client.reload(obj=self.scope_ref_prop)

        self.assertFalse(
            self.scope_ref_prop is reloaded_prop,
            msg="Must be different Python objects, based on memory allocation",
        )
        self.assertEqual(
            self.scope_ref_prop,
            reloaded_prop,
            msg="Must be the same KE-chain prop, based on hashed UUID",
        )

    def test_prefilters(self):
        live_filters = self.scope_ref_prop.get_prefilters()
        self.assertFalse(live_filters)

        tags = ["project", "catalog"]
        filters = [ScopeFilter(tag=tag) for tag in tags]

        self.scope_ref_prop.set_prefilters(
            prefilters=filters,
        )
        self.scope_ref_prop.refresh()
        live_filters = self.scope_ref_prop.get_prefilters()

        self.assertTrue(live_filters)
        self.assertIsInstance(live_filters, list)
        self.assertTrue(all(isinstance(pf, ScopeFilter) for pf in live_filters))

        self.scope_ref_prop.set_prefilters(clear=True)
        self.scope_ref_prop.refresh()
        live_filters = self.scope_ref_prop.get_prefilters()
        self.assertFalse(live_filters)

        with self.assertRaises(IllegalArgumentError):
            # noinspection PyTypeChecker
            self.scope_ref_prop.set_prefilters(prefilters=filters[0])


class TestPropertyUserReference(TestBetamax):
    def setUp(self):
        super().setUp()
        root = self.project.model(name="Product")

        self.part = self.project.create_model(
            name="Test part", parent=root, multiplicity=Multiplicity.ONE
        )
        self.user_ref_prop = self.part.add_property(
            name="user ref", property_type=PropertyType.USER_REFERENCES_VALUE
        )

    def tearDown(self):
        if self.part:
            self.part.delete()
        super().tearDown()

    def test_create(self):
        self.assertIsInstance(self.user_ref_prop, UserReferencesProperty)

    def test_value(self):
        user = self.client.user(name="User Test")

        self.user_ref_prop.value = [user]

        self.assertIsInstance(self.user_ref_prop, UserReferencesProperty)
        self.assertIsNotNone(self.user_ref_prop.value)
        self.assertEqual(user, self.user_ref_prop.value[0])

    def test_value_ids(self):
        user = self.client.user(name="User Test")

        self.user_ref_prop.value = [user]

        self.user_ref_prop.refresh()

        ids = self.user_ref_prop.value_ids()

        self.assertIsInstance(ids, list)
        self.assertTrue(all(isinstance(v, int) for v in ids))

    def test_no_value(self):
        self.assertIsInstance(self.user_ref_prop, UserReferencesProperty)
        self.assertIsNone(self.user_ref_prop.value)

    def test_reload(self):
        reloaded_prop = self.client.reload(obj=self.user_ref_prop)

        self.assertFalse(
            self.user_ref_prop is reloaded_prop,
            msg="Must be different Python objects, based on memory allocation",
        )
        self.assertEqual(
            self.user_ref_prop,
            reloaded_prop,
            msg="Must be the same KE-chain prop, based on hashed UUID",
        )


class TestPropertyFormReference(TestBetamax):
    def setUp(self):
        super().setUp()
        root = self.project.model(name="Product")
        self.part = self.project.create_model(
            name="TEST_FORM_REFERENCE_PART", parent=root, multiplicity=Multiplicity.ONE
        )
        self.form_ref_prop_model = self.part.add_property(
            name="form ref", property_type=PropertyType.FORM_REFERENCES_VALUE
        )
        self.workflow = self.client.workflow(
            name="Simple Form Flow", category=WorkflowCategory.CATALOG
        )
        self.approval_workflow = self.client.workflow(
            name="Strict Approval Workflow", category=WorkflowCategory.CATALOG
        )
        self.discipline_context = self.project.context(name="Discipline 1")
        self.asset_context = self.project.context(name="Object 1")
        self.form_model_name = "__TEST__FORM_MODEL"
        self.form_model = self.client.create_form_model(
            name=self.form_model_name,
            scope=self.project,
            workflow=self.workflow,
            category=FormCategory.MODEL,
            contexts=[self.asset_context, self.discipline_context],
        )
        self.form_ref_prop_instance = self.part.instance().property(
            name=self.form_ref_prop_model.name
        )
        self.form_instance_1 = self.form_model.instantiate(
            name="__FIRST_TEST_FORM_INSTANCE"
        )
        self.form_instance_2 = self.form_model.instantiate(
            name="__SECOND_TEST_FORM_INSTANCE "
        )

    def tearDown(self):
        if self.part:
            self.part.delete()
        if self.form_instance_1:
            self.form_instance_1.delete()
        if self.form_instance_2:
            self.form_instance_2.delete()
        if self.form_model:
            self.form_model.delete()
        super().tearDown()

    def test_create(self):
        self.assertIsInstance(self.form_ref_prop_model, FormReferencesProperty)

    def test_value_model(self):
        self.form_ref_prop_model.value = [self.form_model]

        self.assertIsNotNone(self.form_ref_prop_model.value)
        self.assertEqual(self.form_ref_prop_model.value[0].id, self.form_model.id)
        self.assertEqual(len(self.form_ref_prop_model.value), 1)

    def test_no_value_model(self):
        self.assertIsInstance(self.form_ref_prop_model, FormReferencesProperty)
        self.assertIsNone(self.form_ref_prop_model.value)

    def test_value_instance(self):
        self.form_ref_prop_model.value = [self.form_model]
        self.form_ref_prop_instance.value = [self.form_instance_1]

        self.assertEqual(len(self.form_ref_prop_instance.value), 1)
        self.assertEqual(
            self.form_ref_prop_instance.value[0].id, self.form_instance_1.id
        )

        self.form_ref_prop_instance.value = [self.form_instance_1, self.form_instance_2]

        self.assertEqual(len(self.form_ref_prop_instance.value), 2)

        self.assertIn(
            self.form_instance_1.id,
            [value.id for value in self.form_ref_prop_instance.value],
        )
        self.assertIn(
            self.form_instance_2.id,
            [value.id for value in self.form_ref_prop_instance.value],
        )


class TestPropertyContextReference(TestBetamax):
    def setUp(self):
        super().setUp()
        root = self.project.model(name="Product")
        self.part = self.project.create_model(
            name="TEST_CONTEXT_REFERENCE_PART",
            parent=root,
            multiplicity=Multiplicity.ONE,
        )
        self.context_ref_prop_model = self.part.add_property(
            name="context ref", property_type=PropertyType.CONTEXT_REFERENCES_VALUE
        )
        self.context_ref_prop_instance = self.part.instance().property(
            name=self.context_ref_prop_model.name
        )

        self.context_1 = self.client.create_context(
            name="__testing_context_1",
            context_type=ContextType.TIME_PERIOD,
            context_group=ContextGroup.DISCIPLINE,
            scope=self.project.id,
            tags=["testing"],
        )  # type: Context
        self.context_2 = self.client.create_context(
            name="__testing_context_2",
            context_type=ContextType.STATIC_LOCATION,
            context_group=ContextGroup.LOCATION,
            scope=self.project.id,
            tags=["testing"],
        )  # type: Context

    def tearDown(self):
        if self.part:
            self.part.delete()
        if self.context_1:
            self.context_1.delete()
        if self.context_2:
            self.context_2.delete()
        super().tearDown()

    def test_create(self):
        self.assertIsInstance(self.context_ref_prop_model, ContextReferencesProperty)

    def test_value_model(self):
        self.context_ref_prop_model.value = [self.context_1]

        self.assertIsNotNone(self.context_ref_prop_model.value)
        self.assertEqual(self.context_ref_prop_model.value[0].id, self.context_1.id)
        self.assertEqual(len(self.context_ref_prop_model.value), 1)

    def test_no_value_model(self):
        self.assertIsNone(self.context_ref_prop_model.value)

    def test_value_instance(self):
        self.context_ref_prop_instance.value = [self.context_1]

        self.assertIsNotNone(self.context_ref_prop_instance.value)
        self.assertEqual(self.context_ref_prop_instance.value[0].id, self.context_1.id)
        self.assertEqual(len(self.context_ref_prop_instance.value), 1)

    def test_no_value_instance(self):
        self.assertIsNone(self.context_ref_prop_instance.value)

    def test_multiple_values(self):
        self.context_ref_prop_instance.value = [self.context_1, self.context_2]

        self.assertEqual(len(self.context_ref_prop_instance.value), 2)
        self.assertIn(
            self.context_1.id,
            [value.id for value in self.context_ref_prop_instance.value],
        )
        self.assertIn(
            self.context_2.id,
            [value.id for value in self.context_ref_prop_instance.value],
        )


class TestPropertyStatusReferences(TestBetamax):
    def setUp(self):
        super().setUp()
        root = self.project.model(name="Product")
        self.part = self.project.create_model(
            name="TEST_STATUS_REFERENCE_PART",
            parent=root,
            multiplicity=Multiplicity.ONE,
        )
        self.status_ref_prop_model = self.part.add_property(
            name="status ref", property_type=PropertyType.STATUS_REFERENCES_VALUE
        )
        self.status_ref_prop_instance = self.part.instance().property(
            name=self.status_ref_prop_model.name
        )

        self.status_1: Status = Status.get(client=self.client, name="To Do")
        self.status_2: Status = Status.get(client=self.client, name="Done")

    def tearDown(self):
        if self.part:
            self.part.delete()
        super().tearDown()

    def test_create(self):
        self.assertIsInstance(self.status_ref_prop_model, StatusReferencesProperty)

    def test_value_model(self):
        self.status_ref_prop_model.value = [self.status_1]

        self.assertIsNotNone(self.status_ref_prop_model.value)
        self.assertEqual(self.status_ref_prop_model.value[0].id, self.status_1.id)
        self.assertEqual(len(self.status_ref_prop_model.value), 1)

    def test_no_value_model(self):
        self.assertIsNone(self.status_ref_prop_model.value)

    def test_value_instance(self):
        self.status_ref_prop_instance.value = [self.status_1]

        self.assertIsNotNone(self.status_ref_prop_instance.value)
        self.assertEqual(self.status_ref_prop_instance.value[0].id, self.status_1.id)
        self.assertEqual(len(self.status_ref_prop_instance.value), 1)

    def test_no_value_instance(self):
        self.assertIsNone(self.status_ref_prop_instance.value)

    def test_multiple_values(self):
        self.status_ref_prop_instance.value = [self.status_1, self.status_2]

        self.assertEqual(len(self.status_ref_prop_instance.value), 2)
        self.assertIn(
            self.status_1.id,
            [value.id for value in self.status_ref_prop_instance.value],
        )
        self.assertIn(
            self.status_2.id,
            [value.id for value in self.status_ref_prop_instance.value],
        )

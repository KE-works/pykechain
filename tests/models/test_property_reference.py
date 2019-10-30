import datetime
import uuid

from pykechain.enums import PropertyType, FilterType, Multiplicity
from pykechain.exceptions import IllegalArgumentError
from pykechain.models import MultiReferenceProperty2
from pykechain.models.validators import RequiredFieldValidator
from tests.classes import TestBetamax


class TestMultiReferenceProperty(TestBetamax):
    def setUp(self):
        super(TestMultiReferenceProperty, self).setUp()

        # reference Part target (model and 1 instance)
        _wheel_model = self.project.model(ref='wheel')

        self.ref_target_model = self.project.create_model_with_properties(
            parent=_wheel_model.parent_id,
            name="__Wheel",
            multiplicity=Multiplicity.ONE_MANY,
            properties_fvalues = [
                dict(name='__Fabrication date', property_type=PropertyType.DATETIME_VALUE),
                dict(name='__Tyre manufacturer', property_type=PropertyType.SINGLE_SELECT_VALUE),
                dict(name='__Flat tire', property_type=PropertyType.BOOLEAN_VALUE),
                dict(name='__Diameter', property_type=PropertyType.FLOAT_VALUE),
                dict(name='__Spokes', property_type=PropertyType.INT_VALUE),
                dict(name='__Rim Material', property_type=PropertyType.CHAR_VALUE)
            ]
        )
          # integer property

        # reference property model (with a value pointing to a reference target part model
        self.part_model = self.project.model('Bike')

        self.ref_target_datetime_prop = self.ref_target_model.property('__fabrication-date')
        self.ref_target_ssl_prop = self.ref_target_model.add_property('__tyre-manufacturer')
        self.ref_target_bool_prop = self.ref_target_model.add_property('__flat-tyre')
        self.ref_target_diameter_prop = self.ref_target_model.property('__diameter')
        self.ref_target_spokes_prop = self.ref_target_model.property('__spokes')
        self.ref_target_material_prop = self.ref_target_model.property('__rim-material')

        self.ref_prop_name = '__Test reference property'
        self.ref_prop_model = self.part_model.add_property(
            name=self.ref_prop_name,
            property_type=PropertyType.REFERENCES_VALUE,
            default_value=self.ref_target_model.id
        )  # type: MultiReferenceProperty2

        # reference property instance (holding the value
        self.ref = self.part_model.instance().property(self.ref_prop_name)

    def tearDown(self):
        self.ref_target_model.delete()
        self.ref_prop_model.delete()
        super(TestMultiReferenceProperty, self).tearDown()

    def test_referencing_a_model(self):
        # setUp
        wheel_model = self.project.model('Wheel')
        self.ref_prop_model.value = [wheel_model]

        # testing
        self.assertEqual(len(self.ref_prop_model.value), 1)

    def test_referencing_multiple_instances_using_parts(self):
        # setUp
        wheel_model = self.project.model('Wheel')
        self.ref_prop_model.value = [wheel_model]
        wheel_instances = wheel_model.instances()
        wheel_instances_list = [instance for instance in wheel_instances]

        # set ref value
        self.ref.value = wheel_instances_list

        # testing
        self.assertTrue(len(self.ref.value) >= 2)

        # tearDown
        self.ref.value = None

    def test_referencing_multiple_instances_using_ids(self):
        # setUp
        wheel_model = self.project.model('Wheel')
        self.ref_prop_model.value = [wheel_model]
        wheel_instances = wheel_model.instances()
        wheel_instances_list = [instance.id for instance in wheel_instances]

        # set ref value
        self.ref.value = wheel_instances_list
        self.ref._cached_values = None

        # testing
        self.assertTrue(len(self.ref.value) >= 2)

        # tearDown
        self.ref.value = None

    def test_referencing_a_part_not_in_a_list(self):
        # setUp
        front_wheel = self.project.part('Front Wheel')

        # testing
        with self.assertRaises(ValueError):
            self.ref.value = front_wheel

    def test_referencing_a_list_with_no_parts(self):
        # setUp
        fake_part = [15, 21, 26]

        # testing
        with self.assertRaises(ValueError):
            self.ref.value = fake_part

    def test_value_if_multi_ref_gives_back_all_parts(self):
        """because of #276 problem"""
        # setUp
        self.ref_prop_model.value = [self.ref_target_model]

        wheel_instances = self.ref_target_model.instances()
        wheel_instances_list = [instance.id for instance in wheel_instances]

        # set ref value
        self.ref.value = wheel_instances_list
        self.ref.refresh()

        # testing
        all_referred_parts = self.ref.value
        self.assertEqual(len(all_referred_parts), len(self.ref._value))

        # tearDown
        self.ref.value = None

    def test_value_if_nothing_is_referenced(self):
        # setUp
        value_of_multi_ref = self.ref.value

        # testing
        self.assertIsNone(value_of_multi_ref)

    def test_multi_ref_choices(self):
        # setUp
        second_wheel = self.project.part(ref='bike').add(model=self.ref_target_model, name='__Wheel 2')

        # testing
        self.ref_prop_model.value = [self.ref_target_model]
        possible_options = self.ref.choices()
        self.assertEqual(2, len(possible_options))


    def test_create_ref_property_referencing_part_in_list(self):
        # setUp
        new_reference_to_wheel = self.part_model.add_property(
            name=self.ref_prop_name,
            property_type=PropertyType.REFERENCES_VALUE,
            default_value=[self.ref_target_model]
        )
        # testing
        self.assertTrue(self.ref_prop_model.value[0].id, self.ref_target_model.id)

        # tearDown
        new_reference_to_wheel.delete()

    def test_create_ref_property_referencing_id_in_list(self):
        # setUp
        new_reference_to_wheel = self.part_model.add_property(
            name=self.ref_prop_name,
            property_type=PropertyType.REFERENCES_VALUE,
            default_value=[self.ref_target_model.id]
        )
        # testing
        self.assertTrue(self.ref_prop_model.value[0].id, self.ref_target_model.id)

        # tearDown
        new_reference_to_wheel.delete()

    def test_create_ref_property_wrongly_referencing_in_list(self):
        # testing
        with self.assertRaises(IllegalArgumentError):
            self.part_model.add_property(
                name=self.ref_prop_name,
                property_type=PropertyType.REFERENCES_VALUE,
                default_value=[12]
            )

    def test_create_ref_property_referencing_part(self):
        # setUp
        new_reference_to_wheel = self.part_model.add_property(
            name=self.ref_prop_name,
            property_type=PropertyType.REFERENCES_VALUE,
            default_value=self.ref_target_model
        )
        # testing
        self.assertTrue(self.ref_prop_model.value[0].id, self.ref_target_model.id)

        # tearDown
        new_reference_to_wheel.delete()

    def test_create_ref_property_referencing_id(self):
        # setUp
        new_reference_to_wheel = self.part_model.add_property(
            name=self.ref_prop_name,
            property_type=PropertyType.REFERENCES_VALUE,
            default_value=self.ref_target_model.id
        )
        # testing
        self.assertTrue(self.ref_prop_model.value[0].id, self.ref_target_model.id)

        # tearDown
        new_reference_to_wheel.delete()

    def test_create_ref_property_wrongly_referencing(self):
        # testing
        with self.assertRaises(IllegalArgumentError):
            self.part_model.add_property(
                name=self.ref_prop_name,
                property_type=PropertyType.REFERENCES_VALUE,
                default_value=True
            )

    # new in 3.0
    def test_set_prefilters_on_reference_property(self):
        # setUp
        diameter_property = self.ref_target_diameter_prop # decimal property
        spokes_property = self.ref_target_spokes_prop  # integer property
        rim_material_property = self.ref_target_material_prop  # single line text

        self.ref_prop_model.set_prefilters(
            property_models=[diameter_property,
                             spokes_property,
                             rim_material_property,
                             self.ref_target_datetime_prop,
                             self.ref_target_ssl_prop,
                             self.ref_target_bool_prop],
            values=[30.5,
                    7,
                    'Al',
                    datetime.datetime.now(),
                    'Michelin',
                    True],
            filters_type=[FilterType.GREATER_THAN_EQUAL,
                          FilterType.LOWER_THAN_EQUAL,
                          FilterType.CONTAINS,
                          FilterType.GREATER_THAN_EQUAL,
                          FilterType.CONTAINS,
                          FilterType.EXACT]
        )

        # testing
        self.assertTrue('property_value' in self.ref_prop_model._options['prefilters'])
        self.assertTrue("{}:{}:{}".format(diameter_property.id, 30.5, FilterType.GREATER_THAN_EQUAL) in
                        self.ref_prop_model._options['prefilters']['property_value'])
        self.assertTrue("{}:{}:{}".format(spokes_property.id, 7, FilterType.LOWER_THAN_EQUAL) in
                        self.ref_prop_model._options['prefilters']['property_value'])
        self.assertTrue("{}:{}:{}".format(rim_material_property.id, 'Al', FilterType.CONTAINS) in
                        self.ref_prop_model._options['prefilters']['property_value'])
        self.assertTrue("{}:{}:{}".format(self.ref_target_bool_prop.id, 'True', FilterType.EXACT) in
                        self.ref_prop_model._options['prefilters']['property_value'])
        # TODO - fix KEC-20504 and then check for DATETIME
        self.assertTrue("{}:{}:{}".format(self.ref_target_ssl_prop.id, 'Michelin', FilterType.CONTAINS) in
                        self.ref_prop_model._options['prefilters']['property_value'])

    def test_set_prefilters_on_reference_property_with_excluded_propmodels_and_validators(self):
        # The excluded propmodels and validators already set on the property should not be erased when
        # setting prefilters

        # setUp
        diameter_property = self.ref_target_diameter_prop
        spokes_property = self.ref_target_spokes_prop

        self.ref_prop_model.set_excluded_propmodels(property_models=[diameter_property, spokes_property])
        self.ref_prop_model.validators = [RequiredFieldValidator()]

        self.ref_prop_model.set_prefilters(
            property_models=[diameter_property],
            values=[15.13],
            filters_type=[FilterType.GREATER_THAN_EQUAL]
        )

        # testing
        self.assertTrue('property_value' in self.ref_prop_model._options['prefilters'])
        self.assertTrue("{}:{}:{}".format(diameter_property.id, 15.13, FilterType.GREATER_THAN_EQUAL) in
                        self.ref_prop_model._options['prefilters']['property_value'])
        self.assertEqual(len(self.ref_prop_model._options['propmodels_excl']), 2)
        self.assertTrue(diameter_property.id in self.ref_prop_model._options['propmodels_excl'])
        self.assertTrue(spokes_property.id in self.ref_prop_model._options['propmodels_excl'])
        self.assertTrue(isinstance(self.ref_prop_model._validators[0], RequiredFieldValidator))

    def test_add_prefilters_to_reference_property(self):
        # Set the initial prefilters
        self.ref_prop_model.set_prefilters(
            property_models=[self.ref_target_diameter_prop],
            values=[15.13],
            filters_type=[FilterType.GREATER_THAN_EQUAL]
        )
        # Add others, checks whether the initial ones are remembered (overwrite = False)
        self.ref_prop_model.set_prefilters(
            property_models=[self.ref_target_spokes_prop],
            values=[2],
            filters_type=[FilterType.LOWER_THAN_EQUAL],
            overwrite=False
        )

        # testing
        self.assertTrue('property_value' in self.ref_prop_model._options['prefilters'])
        self.assertTrue("{}:{}:{}".format(self.ref_target_diameter_prop.id, 15.13, FilterType.GREATER_THAN_EQUAL) in
                        self.ref_prop_model._options['prefilters']['property_value'])
        self.assertTrue("{}:{}:{}".format(self.ref_target_spokes_prop.id, 2, FilterType.LOWER_THAN_EQUAL) in
                        self.ref_prop_model._options['prefilters']['property_value'])

    def test_overwrite_prefilters_on_reference_property(self):
        # setUp
        diameter_property = self.ref_target_diameter_prop
        spokes_property = self.ref_target_spokes_prop

        # Set the initial prefilters
        self.ref_prop_model.set_prefilters(
            property_models=[diameter_property],
            values=[15.13],
            filters_type=[FilterType.GREATER_THAN_EQUAL]
        )
        # Add others, see if the first ones are remembered (overwrite = False)
        self.ref_prop_model.set_prefilters(
            property_models=[spokes_property],
            values=[2],
            filters_type=[FilterType.LOWER_THAN_EQUAL],
            overwrite=True
        )

        # testing
        self.assertTrue('property_value' in self.ref_prop_model._options['prefilters'])
        self.assertTrue("{}:{}:{}".format(spokes_property.id, 2, FilterType.LOWER_THAN_EQUAL) ==
                        self.ref_prop_model._options['prefilters']['property_value'])

    def test_set_prefilters_on_reference_property_using_uuid(self):
        # setUp
        diameter_property = self.ref_target_diameter_prop
        spokes_property = self.ref_target_spokes_prop

        self.ref_prop_model.set_prefilters(
            property_models=[diameter_property.id,
                             spokes_property.id],
            values=[30.5,
                    7],
            filters_type=[FilterType.GREATER_THAN_EQUAL,
                          FilterType.LOWER_THAN_EQUAL]
        )

        # testing
        self.assertTrue('property_value' in self.ref_prop_model._options['prefilters'])
        self.assertTrue("{}:{}:{}".format(diameter_property.id, 30.5, FilterType.GREATER_THAN_EQUAL) in
                        self.ref_prop_model._options['prefilters']['property_value'])
        self.assertTrue("{}:{}:{}".format(spokes_property.id, 7, FilterType.LOWER_THAN_EQUAL) in
                        self.ref_prop_model._options['prefilters']['property_value'])

    def test_set_prefilters_on_reference_property_the_wrong_way(self):
        # setUp
        bike_gears_property = self.part_model.property(name='Gears')
        instance_diameter_property = self.ref_target_model.instances()[0].property('__diameter')
        diameter_property = self.ref_target_diameter_prop

        # testing
        # When prefilters are being set, but the property does not belong to the referenced part
        with self.assertRaises(IllegalArgumentError):
            self.ref_prop_model.set_prefilters(
                property_models=[bike_gears_property],
                values=[2],
                filters_type=[FilterType.GREATER_THAN_EQUAL]
            )

        # When prefilters are being set, but the property is an instance, not a model
        with self.assertRaises(IllegalArgumentError):
            self.ref_prop_model.set_prefilters(
                property_models=[instance_diameter_property],
                values=[3.33],
                filters_type=[FilterType.GREATER_THAN_EQUAL]
            )

        # When prefilters are being set, but the size of lists is not consistent
        with self.assertRaises(IllegalArgumentError):
            self.ref_prop_model.set_prefilters(
                property_models=[diameter_property],
                values=[3.33, 1.51],
                filters_type=[FilterType.GREATER_THAN_EQUAL, FilterType.CONTAINS]
            )

        # When prefilters are being set, but no UUIDs or `Property` objects are being used in property_models
        with self.assertRaises(IllegalArgumentError):
            self.ref_prop_model.set_prefilters(
                property_models=[False, 301],
                values=[3.33, 1.51],
                filters_type=[FilterType.GREATER_THAN_EQUAL, FilterType.CONTAINS]
            )

    def test_set_excluded_propmodels_on_reference_property(self):
        # setUp
        diameter_property = self.ref_target_diameter_prop
        spokes_property = self.ref_target_spokes_prop

        self.ref_prop_model.set_excluded_propmodels(property_models=[diameter_property, spokes_property])

        # testing
        self.assertEqual(len(self.ref_prop_model._options['propmodels_excl']), 2)
        self.assertTrue(diameter_property.id in self.ref_prop_model._options['propmodels_excl'])
        self.assertTrue(spokes_property.id in self.ref_prop_model._options['propmodels_excl'])

    def test_set_excluded_propmodels_on_reference_property_using_uuid(self):
        # setUp
        diameter_property = self.ref_target_diameter_prop
        spokes_property = self.ref_target_spokes_prop

        self.ref_prop_model.set_excluded_propmodels(property_models=[diameter_property.id, spokes_property.id])

        # testing
        self.assertEqual(len(self.ref_prop_model._options['propmodels_excl']), 2)
        self.assertTrue(diameter_property.id in self.ref_prop_model._options['propmodels_excl'])
        self.assertTrue(spokes_property.id in self.ref_prop_model._options['propmodels_excl'])

    def test_set_excluded_propmodels_on_reference_property_with_prefilters_and_validators(self):
        # The prefilters and validators already set on the property should not be erased when setting
        # excluded propmodels

        # setUp
        diameter_property = self.ref_target_diameter_prop
        spokes_property = self.ref_target_spokes_prop
        self.ref_prop_model.set_prefilters(
            property_models=[diameter_property],
            values=[15.13],
            filters_type=[FilterType.GREATER_THAN_EQUAL]
        )

        self.ref_prop_model.validators = [RequiredFieldValidator()]

        self.ref_prop_model.set_excluded_propmodels(property_models=[diameter_property, spokes_property])

        # testing
        self.assertTrue('property_value' in self.ref_prop_model._options['prefilters'])
        self.assertTrue("{}:{}:{}".format(diameter_property.id, 15.13, FilterType.GREATER_THAN_EQUAL) in
                        self.ref_prop_model._options['prefilters']['property_value'])
        self.assertEqual(len(self.ref_prop_model._options['propmodels_excl']), 2)
        self.assertTrue(diameter_property.id in self.ref_prop_model._options['propmodels_excl'])
        self.assertTrue(spokes_property.id in self.ref_prop_model._options['propmodels_excl'])
        self.assertTrue(isinstance(self.ref_prop_model._validators[0], RequiredFieldValidator))

    def test_set_excluded_propmodels_on_reference_property_the_wrong_way(self):
        # setUp
        bike_gears_property = self.part_model.property(name='Gears')
        instance_diameter_property = self.ref_target_model.instances()[0].property('__diameter')

        # testing
        # When excluded propmodels are being set, but the property does not belong to the referenced part
        with self.assertRaises(IllegalArgumentError):
            self.ref_prop_model.set_excluded_propmodels(property_models=[bike_gears_property])

        # When excluded propmodels are being set, but the property is an instance, not a model
        with self.assertRaises(IllegalArgumentError):
            self.ref_prop_model.set_excluded_propmodels(property_models=[instance_diameter_property])

        # When excluded propmodels are being set, but no UUIDs or `Property` objects are being used in property_models
        with self.assertRaises(IllegalArgumentError):
            self.ref_prop_model.set_excluded_propmodels(property_models=[False, 301])

    def test_add_excluded_propmodels_to_reference_property(self):
        # Set the initial excluded propmodels
        self.ref_prop_model.set_excluded_propmodels(property_models=[self.ref_target_diameter_prop])

        # Add others, checks whether the initial ones are remembered (overwrite = False)
        self.ref_prop_model.set_excluded_propmodels(property_models=[self.ref_target_spokes_prop], overwrite=False)

        # testing
        self.assertEqual(len(self.ref_prop_model._options['propmodels_excl']), 2)
        self.assertTrue(self.ref_target_diameter_prop.id in self.ref_prop_model._options['propmodels_excl'])
        self.assertTrue(self.ref_target_spokes_prop.id in self.ref_prop_model._options['propmodels_excl'])

    def test_overwrite_excluded_propmodels_on_reference_property(self):
        # setUp
        diameter_property = self.ref_target_diameter_prop
        spokes_property = self.ref_target_spokes_prop

        # Set the initial excluded propmodels
        self.ref_prop_model.set_excluded_propmodels(property_models=[diameter_property])

        # Overwrite them
        self.ref_prop_model.set_excluded_propmodels(property_models=[spokes_property], overwrite=True)

        # testing
        self.assertEqual(len(self.ref_prop_model._options['propmodels_excl']), 1)
        self.assertTrue(diameter_property.id not in self.ref_prop_model._options['propmodels_excl'])
        self.assertTrue(spokes_property.id in self.ref_prop_model._options['propmodels_excl'])

    def test_retrieve_scope_id(self):
        frame = self.project.part(name='Frame')

        ref_to_wheel = frame.property(name='Ref to wheel')

        self.assertEqual(ref_to_wheel.scope_id, self.project.id)


class TestMultiReferencePropertyXScope(TestBetamax):

    def setUp(self):
        super(TestMultiReferencePropertyXScope, self).setUp()
        self.x_scope = self.client.create_scope(name='Cross_reference scope', tags=['x-scope-target'])

        self.part_model = self.project.model('Bike')

        # Create reference property and retrieve its instance
        prop_name = 'cross-scope reference property'
        self.x_reference_model = self.part_model.add_property(
            name=prop_name,
            property_type=PropertyType.REFERENCES_VALUE,
        )
        self.x_reference = self.part_model.instance().property(prop_name)

        # Define target model and create an instance
        product_root = self.x_scope.model('Product')
        self.x_target_model = product_root.add_model(name='Reference target', multiplicity=Multiplicity.ZERO_MANY)
        self.x_target = product_root.instance().add(model=self.x_target_model, name='Target instance')

    def tearDown(self):
        self.x_reference_model.delete()
        self.x_scope.delete()
        super(TestMultiReferencePropertyXScope, self).tearDown()

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

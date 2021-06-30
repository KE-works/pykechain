from datetime import datetime

from pykechain.enums import PropertyType, Category, Multiplicity
from pykechain.exceptions import NotFoundError, APIError, IllegalArgumentError
from pykechain.models import Property
from pykechain.models.validators import SingleReferenceValidator
from tests.classes import TestBetamax


class TestPropertyCreation(TestBetamax):

    def setUp(self):
        super().setUp()
        root = self.project.model(name='Product')
        self.part_model = self.project.create_model(
            name='__Test model',
            parent=root,
            multiplicity=Multiplicity.ONE,
        )
        self.part_instance = self.part_model.instance()

    def tearDown(self):
        self.part_model.delete()
        super().tearDown()

    def test_create_and_delete_property_model(self):
        new_property = self.client.create_property(
            model=self.part_model,
            name='New property',
            description='Nice prop',
            property_type=PropertyType.CHAR_VALUE,
            default_value='EUREKA!',
        )

        # check whether the property has been created and whether it's name and type are correct
        self.part_model.refresh()
        new_prop = self.part_model.property(name='New property')

        self.assertEqual(new_property, new_prop)
        self.assertIsInstance(new_prop, Property)
        self.assertEqual(new_prop.value, 'EUREKA!')
        self.assertEqual(new_prop._json_data['property_type'], PropertyType.CHAR_VALUE)

        # Now delete the property model
        new_property.delete()

        # Retrieve the model again
        self.part_model.refresh()

        # Check whether it still has the property model that has just been deleted
        with self.assertRaises(NotFoundError):
            self.part_model.property('New property')

    def test_create_property_unknown_type(self):
        with self.assertRaises(IllegalArgumentError):
            self.part_model.add_property(name='Incorrect property type', property_type='Incorrect property type')

    def test_create_property_on_instance(self):
        with self.assertRaises(IllegalArgumentError):
            self.client.create_property(name='Properties are created on models only', model=self.part_instance)

    def test_create_property_incorrect_value(self):
        with self.assertRaises(APIError):
            self.part_model.add_property(
                name='Boolean',
                property_type=PropertyType.BOOLEAN_VALUE,
                default_value='Not gonna work',
            )

    # 1.16
    def test_creation_of_all_property_model_types(self):
        # set up
        types = [
            PropertyType.CHAR_VALUE,
            PropertyType.TEXT_VALUE,
            PropertyType.INT_VALUE,
            PropertyType.FLOAT_VALUE,
            PropertyType.BOOLEAN_VALUE,
            PropertyType.DATETIME_VALUE,
            PropertyType.LINK_VALUE,
            PropertyType.DATETIME_VALUE,
            PropertyType.SINGLE_SELECT_VALUE,
            PropertyType.REFERENCES_VALUE,
        ]

        values = [
            'string',
            'text',
            0,
            3.1415,
            False,
            datetime.now().isoformat(sep='T'),
            'https://google.com',
            None,
            None,
            None,
        ]

        for property_type, value in zip(types, values):
            with self.subTest(msg=property_type):
                # setUp
                prop = self.part_model.add_property(
                    name=property_type,
                    property_type=property_type,
                    default_value=value,
                )

                # testing
                if value is not None:
                    self.assertTrue(prop.has_value())
                else:
                    self.assertFalse(prop.has_value())

                # tearDown
                prop.delete()


class TestProperties(TestBetamax):
    def setUp(self):
        super(TestProperties, self).setUp()

        self.wheel_model = self.project.model('Wheel')
        self.bike_model = self.project.model('Bike')
        self.prop_name = "__Test property"
        self.prop_model = self.bike_model.add_property(
            name=self.prop_name,
            property_type=PropertyType.INT_VALUE,
            description='description of the property',
            unit='unit of the property',
            default_value=42,
        )

        self.bike = self.bike_model.instance()
        self.prop = self.bike.property(name=self.prop_name)

    def tearDown(self):
        if self.prop_model:
            self.prop_model.delete()
        super(TestProperties, self).tearDown()

    def test_retrieve_properties(self):
        properties = self.project.properties('Diameter')

        self.assertIsInstance(properties, list)
        self.assertTrue(len(properties) > 0)

    def test_retrieve_property(self):
        prop = self.project.property(name='Cheap?', category=Category.MODEL)

        self.assertIsInstance(prop, Property)
        self.assertTrue(prop)

    def test_retrieve_property_model(self):
        model = self.prop.model()

        self.assertEqual(self.prop_model, model)

        models_model = self.prop_model.model()

        self.assertEqual(self.prop_model, models_model)

    def test_property_attributes(self):
        attributes = ['_client', '_json_data', 'id', 'name', 'created_at', 'updated_at', 'ref',
                      'output', '_value', '_options', 'type', 'category',
                      '_validators']

        obj = self.project.property(name='Cheap?', category=Category.MODEL)
        for attribute in attributes:
            with self.subTest(msg=attribute):
                self.assertTrue(hasattr(obj, attribute),
                                "Could not find '{}' in the object: '{}'".format(attribute, obj.__dict__.keys()))

    def test_retrieve_properties_with_kwargs(self):
        # setUp
        properties_with_kwargs = self.client.properties(part_id=self.bike.id)

        self.assertTrue(properties_with_kwargs)

        # testing
        for prop in properties_with_kwargs:
            with self.subTest(msg=prop.name):
                self.assertEqual(prop.part.id, self.bike.id)

    def test_get_property_by_name(self):
        gears_property = self.project.properties(name='Gears', category=Category.INSTANCE)[0]

        self.assertEqual(self.bike.property('Gears'), gears_property)

    def test_get_property_by_uuid(self):
        gears_id = self.bike.property('Gears').id

        gears_property = self.project.properties(pk=gears_id, category=Category.INSTANCE)[0]

        self.assertEqual(self.bike.property(gears_id), gears_property)

    def test_get_invalid_property(self):
        with self.assertRaises(NotFoundError):
            self.bike.property('Price')

    def test_set_property(self):
        new_value = self.prop.value * 2
        self.assertNotEqual(new_value, self.prop.value)

        self.prop.value = new_value
        refreshed_prop = self.bike.property(name=self.prop_name)

        self.assertEqual(new_value, self.prop.value)
        self.assertEqual(new_value, self.prop._value)
        self.assertEqual(new_value, self.prop._json_data.get('value'))
        self.assertEqual(self.prop, refreshed_prop)
        self.assertEqual(self.prop.value, refreshed_prop.value)

    def test_part_of_property(self):
        bike2 = self.bike.property('Gears').part

        self.assertEqual(self.bike.id, bike2.id)

    # 1.11
    def test_edit_property_model_name(self):
        # setUp
        new_name = 'Cogs'
        self.prop_model.edit(name=new_name)
        reloaded_prop = self.bike_model.property(name=new_name)

        # testing
        self.assertEqual(self.prop_model.id, reloaded_prop.id)
        self.assertEqual(new_name, reloaded_prop.name)
        self.assertEqual(self.prop_model.name, reloaded_prop.name)

        with self.assertRaises(IllegalArgumentError):
            self.prop_model.edit(name=True)

    def test_edit_property_model_description(self):
        # setUp
        new_description = 'Cogs, definitely cogs.'
        self.prop_model.edit(description=new_description)
        reloaded_prop = self.bike_model.property(name=self.prop_name)

        # testing
        self.assertEqual(self.prop_model.id, reloaded_prop.id)
        self.assertEqual(self.prop_model.description, reloaded_prop.description)

        with self.assertRaises(IllegalArgumentError):
            self.prop_model.edit(description=True)

    def test_edit_property_model_unit(self):
        # setUp
        new_unit = 'Totally new units'
        self.prop_model.edit(unit=new_unit)
        reloaded_prop = self.bike_model.property(name=self.prop_name)

        # testing
        self.assertEqual(self.prop_model.id, reloaded_prop.id)
        self.assertEqual(self.prop_model.unit, reloaded_prop.unit)

        with self.assertRaises(IllegalArgumentError):
            self.prop_model.edit(unit=4)

    # test added due to #847 - providing no inputs overwrites values
    def test_edit_property_clear_values(self):
        # setup
        initial_name = 'Property first name'
        initial_description = 'Property created to test clearing values.'
        initial_unit = 'mm'

        self.prop_model.edit(name=initial_name, description=initial_description, unit=initial_unit)

        # Edit without mentioning values, everything should stay the same
        new_name = 'Property second name'
        self.prop_model.edit(name=new_name)

        # testing
        self.assertEqual(self.prop_model.name, new_name)
        self.assertEqual(self.prop_model.description, initial_description)
        self.assertEqual(self.prop_model.unit, initial_unit),

        # Edit with clearing the values, name and status cannot be cleared
        self.prop_model.edit(name=None, description=None, unit=None)

        self.assertEqual(self.prop_model.name, new_name)
        self.assertEqual(self.prop_model.description, str())
        self.assertEqual(self.prop_model.unit, str())

    # 2.5.4
    def test_property_type(self):
        self.assertEqual(PropertyType.INT_VALUE, str(self.prop_model.type))

    def test_property_unit(self):
        self.assertEqual('unit of the property', str(self.prop_model.unit))

    def test_property_description(self):
        self.assertEqual('description of the property', str(self.prop_model.description))

    # 3.0
    def test_copy_property_model(self):
        # setUp
        copied_property = self.prop_model.copy(target_part=self.wheel_model, name='Copied property')

        # testing
        self.assertEqual(copied_property.name, 'Copied property')
        self.assertEqual(copied_property.description, self.prop_model.description)
        self.assertEqual(copied_property.unit, self.prop_model.unit)
        self.assertEqual(copied_property.value, self.prop_model.value)

        # tearDown
        copied_property.delete()

    def test_copy_property_instance(self):
        # setUp
        self.prop.value = 200
        copied_property = self.prop.copy(target_part=self.project.part(name='Front Wheel'),
                                         name='Copied property instance')

        # testing
        self.assertEqual(copied_property.name, 'Copied property instance')
        self.assertEqual(copied_property.description, self.prop.description)
        self.assertEqual(copied_property.unit, self.prop.unit)
        self.assertEqual(copied_property.value, self.prop.value)

        # tearDown
        copied_property.model().delete()

    def test_copy_property_instance_to_model(self):
        with self.assertRaises(IllegalArgumentError):
            self.prop.copy(target_part=self.prop_model)

    def test_move_property_model(self):
        # setUp
        moved_property = self.prop_model.move(target_part=self.wheel_model, name='Moved property')

        # testing
        self.assertEqual(moved_property.name, 'Moved property')
        self.assertEqual(moved_property.description, self.prop_model.description)
        self.assertEqual(moved_property.unit, self.prop_model.unit)
        self.assertEqual(moved_property.value, self.prop_model.value)
        with self.assertRaises(NotFoundError):
            self.project.property(id=self.prop_model.id)

        # tearDown
        # for a correct teardown in the unittest we need to -reassign- the moved one to the self.test_property_model
        self.prop_model = moved_property

    def test_move_property_instance(self):
        # setUp
        moved_property = self.prop.move(target_part=self.wheel_model.instances()[0], name='moved property')

        # testing
        with self.assertRaises(APIError):
            self.project.property(id=self.prop_model.id)

        # tearDown
        # for a correct teardown in the unittest we need to -reassign- the moved one to the self.test_property_model
        self.prop_model = moved_property.model()

    def test_retrieve_properties_with_refs(self):
        # setup
        dual_pad_ref = 'dual-pad'
        dual_pad_name = 'Dual Pad?'
        dual_pad_property = self.project.property(ref=dual_pad_ref)
        dual_pad_property_model = self.project.property(ref=dual_pad_ref, category=Category.MODEL)
        seat_part = self.project.part(name='Seat')
        dual_pad_prop_retrieved_from_seat = seat_part.property(dual_pad_ref)

        # testing
        self.assertIsInstance(dual_pad_property, Property)
        self.assertEqual(dual_pad_name, dual_pad_property.name)
        self.assertEqual(Category.INSTANCE, dual_pad_property.category)

        self.assertIsInstance(dual_pad_property_model, Property)
        self.assertEqual(dual_pad_name, dual_pad_property_model.name)
        self.assertEqual(Category.MODEL, dual_pad_property_model.category)

        self.assertIsInstance(dual_pad_prop_retrieved_from_seat, Property)
        self.assertEqual(dual_pad_name, dual_pad_prop_retrieved_from_seat.name)
        self.assertEqual(Category.INSTANCE, dual_pad_prop_retrieved_from_seat.category)

        self.assertEqual(dual_pad_property.id, dual_pad_prop_retrieved_from_seat.id)


class TestUpdateProperties(TestBetamax):
    def setUp(self):
        super().setUp()

        self.bike = self.project.model('Bike')
        self.submodel = self.project.create_model(name='_test submodel', parent=self.bike)

        self.prop_1 = self.submodel.add_property(name=PropertyType.CHAR_VALUE, property_type=PropertyType.CHAR_VALUE)
        self.prop_2 = self.submodel.add_property(name=PropertyType.TEXT_VALUE, property_type=PropertyType.TEXT_VALUE)
        self.props = [self.prop_1, self.prop_2]

    def tearDown(self):
        self.submodel.delete()
        super().tearDown()

    def _refresh_prop(self, p):
        return self.client.property(pk=p.id, category=p.category)

    def test_bulk_update(self):
        """Test the API using the Client method."""
        update = [dict(id=p.id, value='new value') for p in self.props]

        updated_properties = self.client.update_properties(properties=update)

        # testing
        self.assertIsInstance(updated_properties, list)
        self.assertTrue(all(p1 == p2 for p1, p2 in zip(self.props, updated_properties)))
        self.assertTrue(all(isinstance(p, Property) for p in updated_properties))
        self.assertTrue(all(p.value == 'new value' for p in updated_properties))

    def test_bulk_update_manual(self):
        """Test storing of value updates in the Property class."""
        # setUp
        Property.set_bulk_update(True)
        self.prop_1.value = 'new value'
        self.prop_2.value = 'another value'

        # testing
        self.assertIsNone(self._refresh_prop(self.prop_1).value)
        self.assertIsNone(self._refresh_prop(self.prop_2).value)

        Property.update_values(client=self.client)

        self.assertEqual(self._refresh_prop(self.prop_1).value, 'new value')
        self.assertEqual(self._refresh_prop(self.prop_2).value, 'another value')

    def test_bulk_update_reset(self):
        """Test whether bulk update is reset to `False` after update is performed."""
        # setUp
        Property.set_bulk_update(True)
        self.prop_1.value = 'new value'

        # testing
        self.assertIsNone(self._refresh_prop(self.prop_1).value)
        Property.update_values(client=self.client)
        self.assertEqual(self._refresh_prop(self.prop_1).value, 'new value')
        self.assertFalse(Property._USE_BULK_UPDATE)

        # setUp 2
        Property.set_bulk_update(True)
        self.prop_2.value = 'another value'

        # testing 2
        self.assertIsNone(self._refresh_prop(self.prop_2).value)
        Property.update_values(client=self.client, use_bulk_update=True)
        self.assertEqual(self._refresh_prop(self.prop_2).value, 'another value')
        self.assertTrue(Property._USE_BULK_UPDATE)

        # tearDown
        Property.set_bulk_update(False)


class TestPropertiesWithReferenceProperty(TestBetamax):
    def setUp(self):
        super(TestPropertiesWithReferenceProperty, self).setUp()

        self.wheel_model = self.project.model('Wheel')
        self.bike = self.project.model('Bike')

        self.test_ref_property_model = self.bike.add_property(name="__Test ref property @ {}".format(datetime.now()),
                                                              property_type=PropertyType.REFERENCES_VALUE,
                                                              description='Description of test ref property',
                                                              unit='no unit',
                                                              default_value=[self.wheel_model])
        self.test_ref_property_model.validators = [SingleReferenceValidator()]

    def tearDown(self):
        self.test_ref_property_model.delete()
        super(TestPropertiesWithReferenceProperty, self).tearDown()

    def test_copy_reference_property_with_options(self):
        # setUp
        copied_ref_property = self.test_ref_property_model.copy(target_part=self.wheel_model,
                                                                name='__Copied ref property')

        # testing
        self.assertEqual(copied_ref_property.name, '__Copied ref property')
        self.assertEqual(copied_ref_property.description, self.test_ref_property_model.description)
        self.assertEqual(copied_ref_property.unit, self.test_ref_property_model.unit)
        self.assertEqual(copied_ref_property.value, self.test_ref_property_model.value)
        self.assertEqual(copied_ref_property._options, self.test_ref_property_model._options)

        # tearDown
        copied_ref_property.delete()

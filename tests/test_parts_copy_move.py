from datetime import datetime

from pykechain.enums import Multiplicity, PropertyType
from pykechain.exceptions import NotFoundError, IllegalArgumentError
from tests.classes import TestBetamax


class TestPartsCopyMove(TestBetamax):

    def setUp(self):
        super(TestPartsCopyMove, self).setUp()
        self.base = self.project.model(name__startswith='Catalog')
        self.cross_scope_project = self.client.scope(ref='cannondale-project')
        self.cross_scope_bike = self.cross_scope_project.model(ref='cannondale-bike')
        self.cross_scope_wheel = self.cross_scope_bike.add_model(name='__Wheel')

        self.model_to_be_copied = self.project.create_model(
            parent=self.base, name='__Model to be Copied @ {} [TEST]'.format(str(datetime.now())),
            multiplicity=Multiplicity.ONE_MANY)  # type Part
        p_char = self.model_to_be_copied.add_property(
            name='__Property single text',
            description='Description of Property single text',
            unit='mm',
            property_type=PropertyType.CHAR_VALUE
        )
        p_decimal = self.model_to_be_copied.add_property(
            name='__Property decimal number',
            default_value=33,
            property_type=PropertyType.FLOAT_VALUE
        )
        p_single_select = self.model_to_be_copied.add_property(
            name='__Property single select list',
            options=dict(value_choices=['a', 'b', 'c']),
            property_type=PropertyType.SINGLE_SELECT_VALUE
        )
        p_multi_reference_property = self.model_to_be_copied.add_property(
            name='__Property multi reference',
            default_value=self.cross_scope_wheel,
            # options={S},
            property_type=PropertyType.REFERENCES_VALUE
        )
        sub_part1 = self.model_to_be_copied.add_model(
            name="__subpart 1",
            multiplicity=Multiplicity.ONE
        )
        sub_part2 = self.model_to_be_copied.add_model(
            name="__subpart 2",
            multiplicity=Multiplicity.ONE
        )

        self.model_target_parent = self.project.model(ref='bike')
        self.instance_to_be_copied = self.model_to_be_copied.instances()[0]
        self.instance_target_parent = self.model_to_be_copied.parent().instances()[0]
        self.dump_part = None

    def tearDown(self):
        self.model_to_be_copied.delete()
        self.cross_scope_wheel.delete()
        if self.dump_part:
            self.dump_part.delete()
        super(TestPartsCopyMove, self).tearDown()

    def test_copy_part_model_given_name_include_children(self):
        model_target_parent = self.project.model('Bike')
        copied_model = self.model_to_be_copied.copy(
            target_parent=model_target_parent,
            name='__Copied model under Bike',
            include_children=True,
            include_instances=False
        )
        copied_model.populate_descendants()
        self.dump_part = copied_model

        # testing
        self.assertTrue(copied_model)
        self.assertEqual(copied_model.property('__Property single text')._json_data['description'],
                         'Description of Property single text')
        self.assertEqual(copied_model.property('__Property single text')._json_data['unit'], 'mm')
        self.assertEqual(copied_model.property('__Property decimal number').value, 33)
        self.assertEqual(copied_model.property('__Property single select list').options, ['a', 'b', 'c'])
        self.assertEqual(len(copied_model._cached_children), 2)

    def test_copy_part_model_include_instances(self):
        model_target_parent = self.project.model('Bike')
        self.dump_part = self.model_to_be_copied.copy(
            target_parent=model_target_parent,
            name='__Copied model under Bike',
            include_children=True,
            include_instances=True
        )
        bike_part = self.project.part('Bike')

        copied_instance = [child for child in bike_part.children() if 'to be Copied' in child.name][0]
        copied_instance.populate_descendants()

        # testing
        self.assertTrue(copied_instance)
        self.assertEqual(len(copied_instance.properties), 4)
        self.assertTrue(copied_instance.property('__property-single-text'))
        self.assertEqual(copied_instance.property('__property-decimal-number').value, 33)
        self.assertEqual(copied_instance.property('__property-single-select-list').value, None)

        self.assertEqual(len(copied_instance._cached_children), 2)

    def test_copy_part_model_empty_name_not_include_children(self):
        # setUp
        model_target_parent = self.project.model('Bike')
        name_of_part = '__Copied model under Bike'
        copied_model = self.model_to_be_copied.copy(
            target_parent=model_target_parent,
            name=name_of_part,
            include_children=False,
            include_instances=False
        )

        copied_model.populate_descendants()
        self.dump_part = copied_model

        # testing
        self.assertTrue(copied_model)
        self.assertEqual(copied_model.name, name_of_part)
        self.assertEqual(len(copied_model.properties), 4)
        self.assertEqual(len(copied_model._cached_children), 0)

    def test_move_part_model(self):
        # setUp
        model_target_parent = self.project.model('Bike')
        clone_of_original_model = self.model_to_be_copied.clone()
        self.assertEqual(clone_of_original_model.name, 'CLONE - {}'.format(self.model_to_be_copied.name))

        clone_of_original_model.move(target_parent=model_target_parent,
                                     name='__New part under bike',
                                     include_children=True)

        self.dump_part = self.project.model(name='__New part under bike')

        # testing
        with self.assertRaises(NotFoundError):
            self.project.model(name=clone_of_original_model.name)

    def test_copy_part_instance(self):
        # setUp
        instance_to_be_copied = self.model_to_be_copied.instances()[0]
        instance_target_parent = self.project.part('Bike')
        instance_to_be_copied.copy(target_parent=instance_target_parent, name='__Copied instance', include_children=True)

        copied_instance = self.project.part(name='__Copied instance')
        copied_instance.populate_descendants()
        self.dump_part = copied_instance.model()

        # testing
        self.assertTrue(copied_instance)
        self.assertEqual(copied_instance.name, '__Copied instance')
        self.assertEqual(len(copied_instance.properties), len(self.model_to_be_copied.properties))
        self.assertEqual(copied_instance.property('__property-single-text').value, None)
        self.assertEqual(copied_instance.property('__property-decimal-number').value, 33)
        self.assertEqual(copied_instance.property('__property-single-select-list').value, None)

        self.assertEqual(len(copied_instance._cached_children), 2)

    def test_move_part_instance(self):
        # setUp
        multiplicity_model = self.model_to_be_copied.add_model(
            name="__multiplicity part",
            multiplicity=Multiplicity.ZERO_MANY
        )
        multiplicity_part1 = self.instance_to_be_copied.add(
            model=multiplicity_model,
            name="__multiplicity part instance 1",
        )
        multiplicity_part2 = self.instance_to_be_copied.add(
            model=multiplicity_model,
            name="__multiplicity part instance 2",
        )

        clone_of_original_instance = multiplicity_part2.clone()

        moved_instance = clone_of_original_instance.move(target_parent=self.project.part('Bike'),
                                                         name='__Moved clone instance',
                                                         include_children=False)

        moved_instance.populate_descendants()
        self.dump_part = moved_instance.model()

        # testing
        with self.assertRaises(NotFoundError):
            self.project.model(name=clone_of_original_instance.name)

        self.assertTrue(moved_instance)
        self.assertEqual(len(moved_instance.properties), 0)
        # self.assertEqual(moved_instance.property('Property multi-text').value, 'Yes yes oh yes')

    def test_copy_different_categories(self):
        target_instance = self.project.part(name='Bike')

        with self.assertRaisesRegex(IllegalArgumentError, 'must have the same category'):
            self.model_to_be_copied.copy(target_parent=target_instance)

    def test_move_different_categories(self):
        target_instance = self.project.part(name='Bike')

        with self.assertRaisesRegex(IllegalArgumentError, 'must have the same category'):
            self.model_to_be_copied.move(target_parent=target_instance)

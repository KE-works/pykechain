from pykechain.exceptions import IllegalArgumentError, APIError
from pykechain.models import Activity2, Part2, Property2
from pykechain.models.association import Association
from pykechain.models.input_checks import check_list_of_base
from pykechain.utils import is_uuid
from tests.classes import TestBetamax


class TestAssociations(TestBetamax):

    def setUp(self):
        super().setUp()
        self.task = self.project.create_activity(name="widget_test_task")  # type: Activity2

        # Exactly 1 model
        self.frame = self.project.part(name='Frame')  # type: Part2
        self.frame_model = self.project.model(name='Frame')

        # Zero or more model
        self.wheel_parent = self.project.model(name='Bike')  # type: Property2
        self.wheel_model = self.project.model(name='Wheel')

        widgets_manager = self.task.widgets()
        self.form_widget = widgets_manager.add_propertygrid_widget(
            part_instance=self.frame,
            readable_models=self.frame_model.properties[:2],
            writable_models=[],
        )

        self.table_widget = widgets_manager.add_supergrid_widget(
            part_model=self.wheel_model,
            parent_instance=self.wheel_parent,
            readable_models=[],
            writable_models=self.frame_model.properties[:2],
        )

    def tearDown(self):
        self.task.delete()
        super().tearDown()

    def test_retrieve_associations_interface(self):
        limit = 3
        associations = self.client.associations(limit=limit)

        self.assertIsInstance(associations, list)
        self.assertEqual(limit, len(associations))
        self.assertTrue(all(isinstance(a, Association) for a in associations))

    def test_association_attributes(self):
        attributes = ['_client', '_json_data', 'id']

        association = self.client.associations(limit=1)[0]
        for attribute in attributes:
            with self.subTest(msg=attribute):
                self.assertTrue(hasattr(association, attribute),
                                "Could not find '{}' in the association: '{}'".format(attribute,
                                                                                      association.__dict__.keys()))

    def test_retrieve_associations(self):
        for inputs, nr in [
            (dict(widget=self.form_widget), 4),
            (dict(activity=self.task), 8),
            (dict(part=self.frame_model), 14),
            (dict(part=self.frame), 10),
            (dict(property=self.frame_model.properties[0]), 6),
            (dict(property=self.frame.properties[0]), 4),
            (dict(scope=self.project), 48)
        ]:
            with self.subTest(msg='{} should be len={}'.format(inputs, nr)):
                # setUp
                associations = self.client.associations(limit=100, **inputs)

                # testing
                self.assertEqual(nr, len(associations))

    def test_retrieve_association_incorrect_inputs(self):
        for keyword, value in dict(
            widget='not a widget',
            activity='not a task',
            part='not a part',
            scope='not a scope',
            property='not a property',
        ).items():
            with self.subTest(msg='{}: "{}"'.format(keyword, value)):
                with self.assertRaises(IllegalArgumentError):
                    self.client.associations(limit=1, **{keyword: value})

        for limit in [-5, '3']:
            with self.subTest('limit: {} {}'.format(type(limit), limit)):
                with self.assertRaises(IllegalArgumentError):
                    self.client.associations(limit=limit)

    def test_update_widget_associations(self):
        original_associations = self.client.associations(widget=self.form_widget)

        self.assertEqual(4, len(original_associations))

        self.client.update_widget_associations(
            widget=self.form_widget,
            readable_models=[],
            writable_models=self.frame_model.properties[2:3],
        )
        associations = self.client.associations(widget=self.form_widget)

        self.assertEqual(6, len(associations))

    def test_update_associations_empty(self):
        self.client.update_widgets_associations(
            widgets=[self.form_widget],
            associations=[([], [])],
        )

    def test_set_associations(self):
        self.client.set_widget_associations(
            widget=self.form_widget,
            readable_models=[],
            writable_models=self.frame_model.properties,
        )

    def test_set_associations_empty(self):
        self.client.set_widgets_associations(
            widgets=[self.form_widget],
            associations=[([], [])],
        )

    def test_clear_associations(self):
        original_associations = self.client.associations(widget=self.form_widget)

        self.assertEqual(4, len(original_associations))

        self.client.clear_widget_associations(widget=self.form_widget)
        associations = self.client.associations(widget=self.form_widget)

        self.assertEqual(0, len(associations))

    def test_remove_associations(self):
        original_associations = self.client.associations(widget=self.form_widget)

        self.assertEqual(4, len(original_associations))

        self.client.remove_widget_associations(
            widget=self.form_widget,
            models=self.frame_model.properties[0:1],
        )
        associations = self.client.associations(widget=self.form_widget)

        self.assertEqual(2, len(associations))

    def test_validate_widgets_input(self):
        with self.assertRaises(IllegalArgumentError, msg='Widget must be a list!'):
            self.client._validate_associations(
                widgets='Not a list',
                associations=[]
            )
        with self.assertRaises(IllegalArgumentError, msg='Not every widget is a widget!'):
            self.client._validate_associations(
                widgets=[self.task.widgets()[0], 'Not a widget'],
                associations=[]
            )
        with self.assertRaises(IllegalArgumentError, msg='Second set of associations is not of length 2!'):
            self.client._validate_associations(
                widgets=list(self.task.widgets()),
                associations=[([], []), ()]
            )
        with self.assertRaises(IllegalArgumentError, msg='Inputs are not of equal length!'):
            self.client._validate_associations(
                widgets=list(self.task.widgets()),
                associations=[([], [])],
            )

    # noinspection PyTypeChecker
    def test_validate_model_input(self):
        model_ids = check_list_of_base(self.frame_model.properties, Property2)

        self.assertIsInstance(model_ids, list)
        self.assertTrue(all(is_uuid(model_id) for model_id in model_ids))
        self.assertEqual(len(self.frame_model.properties), len(model_ids))

        with self.assertRaises(IllegalArgumentError):
            check_list_of_base(objects='not a list')

        with self.assertRaises(IllegalArgumentError):
            check_list_of_base(objects=[self.frame_model.properties[0], 'Not a property'], cls=Property2)

    def test_validate_widget_input(self):
        for method in [
            self.client.update_widget_associations,
            self.client.set_widget_associations,
            self.client.clear_widget_associations,
            self.client.remove_widget_associations,
        ]:
            with self.assertRaises(IllegalArgumentError):
                method(widget='Not a widget')

    def test_readable_models(self):
        self.client.update_widget_associations(
            widget=self.form_widget,
            readable_models=self.frame_model.properties,
        )

        self.client.update_widget_associations(
            widget=self.table_widget,
            readable_models=self.wheel_model.properties,
        )

        with self.assertRaises(APIError):
            self.client.update_widget_associations(
                widget=self.table_widget,
                readable_models=self.frame.properties,
            )

    def test_writable_models(self):
        self.client.update_widget_associations(
            widget=self.form_widget,
            writable_models=self.frame_model.properties,
        )

        self.client.update_widget_associations(
            widget=self.table_widget,
            writable_models=self.wheel_model.properties,
        )

        with self.assertRaises(APIError):
            self.client.update_widget_associations(
                widget=self.table_widget,
                writable_models=self.frame.properties,
            )

from pykechain.enums import PropertyType
from pykechain.exceptions import IllegalArgumentError
from pykechain.models import Property, SelectListProperty
from pykechain.models.property_selectlist import MultiSelectListProperty
from tests.classes import TestBetamax


class SelectListBaseTests:
    """This wrapping class is excluded from the test runs, but can be inherited from."""

    class Tests(TestBetamax):
        """Tests for the select list properties."""

        PROPERTY_TYPE = None
        OPTIONS = ["1", "3.14", "text"]

        def setUp(self):
            super().setUp()

            self.select_model = self.project.model("Bike").add_property(
                name=self.PROPERTY_TYPE,
                property_type=self.PROPERTY_TYPE,
                options={"value_choices": ["1", "3.14", "text"]},
            )
            self.select = self.project.part("Bike").property(self.PROPERTY_TYPE)

        def tearDown(self):
            self.select_model.delete()
            super().tearDown()

        def test_get_options_list(self):
            self.assertTrue(hasattr(self.select_model, "options"))
            self.assertIsInstance(self.select_model.options, list)
            for item in self.select_model.options:
                self.assertTrue(type(item), str)

        def test_set_options_list(self):
            # setUp
            current_options_list = [1, 3.14, "text"]
            new_options_list = ["some", "new", 4, "options"]
            self.select_model.options = new_options_list

            # testing
            self.assertListEqual(
                self.select_model.options, list(map(str, new_options_list))
            )

            # teardown
            self.select_model.options = current_options_list

        def test_illegal_options_are_not_set(self):
            """Test for several illegal lists to be set"""
            with self.assertRaises(IllegalArgumentError):
                # not a list
                self.select_model.options = 1

            with self.assertRaises(IllegalArgumentError):
                self.select_model.options = None

            with self.assertRaises(IllegalArgumentError):
                # set
                self.select_model.options = {1, 2, 3}

            with self.assertRaises(IllegalArgumentError):
                # dict
                self.select_model.options = {"a": 1, "b": 2, "c": 3}

            with self.assertRaises(IllegalArgumentError):
                # tuple
                self.select_model.options = (1,)

        def test_fail_to_set_options_on_instance(self):
            """Test settings options on a property instance, only models are allowed options to be set"""
            self.assertTrue(hasattr(self.select, "options"))

            with self.assertRaises(IllegalArgumentError):
                self.select.options = [1, 3.14]

        def test_integrity_options_dict(self):
            # setUp
            original_options_dict = dict(self.select_model._options)
            self.select_model.options = list(self.select_model.options)

            # testing
            testing_options_dict = self.select_model._options
            self.assertEqual(original_options_dict, testing_options_dict)


class TestPropertySelectListProperty(SelectListBaseTests.Tests):
    PROPERTY_TYPE = PropertyType.SINGLE_SELECT_VALUE

    def test_value(self):
        self.select.value = self.OPTIONS[0]
        self.assertIsInstance(self.select, SelectListProperty)

    def test_pend_value(self):
        self.select.value = None

        Property.set_bulk_update(True)

        self.select.value = self.OPTIONS[1]

        live_property = self.project.property(id=self.select.id)
        self.assertFalse(live_property.has_value())

        Property.update_values(client=self.client)

        live_property.refresh()
        self.assertTrue(live_property.has_value())

    # in 1.16
    def test_set_value_in_options(self):
        # setUp
        current_options_list = self.select_model.options
        first_option = current_options_list[0]
        self.select.value = first_option

        # testing
        option_that_is_set = self.select.value
        self.assertEqual(first_option, option_that_is_set)

    # in 1.15
    def test_set_value_not_in_options_raises_error(self):
        with self.assertRaises(IllegalArgumentError):
            self.select.value = (
                "Some illegal value that is not inside the list of options for sure"
            )


class TestPropertyMultiSelectListProperty(SelectListBaseTests.Tests):
    PROPERTY_TYPE = PropertyType.MULTI_SELECT_VALUE

    def test_value(self):
        self.select.value = self.OPTIONS[0:1]
        self.assertIsInstance(self.select, MultiSelectListProperty)

    # in 1.16
    def test_set_value_in_options(self):
        # setUp
        current_options_list = self.select_model.options
        selection = current_options_list[1:2]
        self.select.value = selection

        # testing
        option_that_is_set = self.select.value
        self.assertEqual(selection, option_that_is_set)

    def test_set_value_not_in_options_raises_error(self):
        with self.assertRaises(IllegalArgumentError):
            self.select.value = [
                "Some illegal value that is not inside the list of options for sure"
            ]

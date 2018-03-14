# -*- coding: utf-8 -*-

from pykechain.exceptions import APIError, IllegalArgumentError
from tests.classes import TestBetamax


class TestSelectListProperty(TestBetamax):
    """Tests for the select list properties"""
    def setUp(self):
        super(TestSelectListProperty, self).setUp()

        self.select = self.project.part('Bike').property('Test single select list property')
        self.select_model = self.project.model('Bike').property('Test single select list property')

    def test_get_options_list(self):
        self.assertTrue(hasattr(self.select_model, 'options'))
        self.assertIsInstance(self.select_model.options, list)
        for item in self.select_model.options:
            self.assertTrue(type(item), str)

    def test_set_options_list(self):
        # setUp
        current_options_list = [1, 3.14, "text"]
        new_options_list = ['some', 'new', 4, 'options']
        self.select_model.options = new_options_list

        # testing
        self.assertListEqual(self.select_model.options, list(map(str, new_options_list)))

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
            self.select_model.options = {'a': 1, 'b': 2, 'c': 3}

        with self.assertRaises(IllegalArgumentError):
            # tuple
            self.select_model.options = (1,)

    def test_fail_to_set_options_on_instance(self):
        """Test settings options on a property instance, only models are allowed options to be set"""
        self.assertTrue(hasattr(self.select, 'options'))

        with self.assertRaises(IllegalArgumentError):
            self.select.options = [1, 3.14]

    # in 1.15
    def test_set_value_not_in_options_raises_error(self):
        with self.assertRaises(APIError):
            self.select.value = 'Some illegal value that is not inside the list of options for sure'

    # in 1.16
    def test_set_value_in_options(self):
        # setUp
        current_options_list = self.select_model.options
        first_option = current_options_list[0]
        self.select.value = first_option

        # testing
        option_that_is_set = self.select.value
        self.assertEqual(first_option, option_that_is_set)

        # tearDown
        self.select.value = None

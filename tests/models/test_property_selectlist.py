# -*- coding: utf-8 -*-

from pykechain.exceptions import APIError
from tests.classes import TestBetamax


class TestSelectListProperty(TestBetamax):
    """Tests for the select list properties"""

    def test_get_options_list(self):
        sellist_model = self.project.model('Model').property('a_select_list_property')
        assert hasattr(sellist_model, 'options')
        assert isinstance(sellist_model.options, list)
        for item in sellist_model.options:
            self.assertTrue(type(item), str)

    def test_set_options_list(self):
        # setup
        sellist_model = self.project.model('Model').property('a_select_list_property')

        saved_options_list = [str(i) for i in sellist_model.options]

        # do test
        from datetime import datetime
        new_options_list = [1, 3.14, "a"]
        sellist_model.options = new_options_list
        self.assertListEqual(sellist_model.options, list(map(str, new_options_list)))

        sellist_model2 = self.project.model('Model').property('a_select_list_property')
        self.assertListEqual(sellist_model.options, sellist_model2.options)

        # teardown
        sellist_model.options = saved_options_list

    def test_illegal_options_are_not_set(self):
        """Test for secveral illegal lists to be set"""
        sellist_model = self.project.model('Model').property('a_select_list_property')
        with self.assertRaises(AssertionError):
            # not a list
            sellist_model.options = 1

        with self.assertRaises(AssertionError):
            sellist_model.options = None

        with self.assertRaises(AssertionError):
            # set
            sellist_model.options = set((1, 2))

        with self.assertRaises(AssertionError):
            # dict
            sellist_model.options = {}

        with self.assertRaises(AssertionError):
            # tuple
            sellist_model.options = (1,)

    def test_fail_to_set_options_on_instance(self):
        """Test settings options on a property instance, only models are allowed optiosn to be set"""
        sellist_model = self.project.model('Model')
        sellist_part_instance = self.project.parts(model=sellist_model)
        sellist_part_instance = sellist_part_instance[0]
        assert sellist_part_instance.category == 'INSTANCE'

        sellist_property = sellist_part_instance.property('a_select_list_property')
        assert hasattr(sellist_property, 'options')

        with self.assertRaises(APIError):
            sellist_property.options = [1, 3.14]

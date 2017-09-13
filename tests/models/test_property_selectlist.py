# -*- coding: utf-8 -*-

from pykechain.exceptions import APIError
from tests.classes import TestBetamax


class TestSelectListProperty(TestBetamax):
    """Tests for the select list properties"""

    def test_get_options_list(self):
        sellist_model = self.project.model('Model').property('a_select_list_property')
        self.assertTrue(hasattr(sellist_model, 'options'))
        self.assertIsInstance(sellist_model.options, list)
        for item in sellist_model.options:
            self.assertTrue(type(item), str)

    def test_set_options_list(self):
        # setup
        sellist_model = self.project.model('Model').property('a_select_list_property')

        # do test
        current_options_list = [1, 3.14, "a"]
        new_options_list = ['this', 'is', 'new']
        sellist_model.options = new_options_list
        self.assertListEqual(sellist_model.options, list(map(str, new_options_list)))

        sellist_model2 = self.project.model('Model').property('a_select_list_property')
        self.assertListEqual(sellist_model.options, sellist_model2.options)

        # teardown
        sellist_model.options = current_options_list

    def test_illegal_options_are_not_set(self):
        """Test for secveral illegal lists to be set"""
        sellist_model = self.project.model('Model').property('a_select_list_property')
        with self.assertRaises(APIError):
            # not a list
            sellist_model.options = 1

        with self.assertRaises(APIError):
            sellist_model.options = None

        with self.assertRaises(APIError):
            # set
            sellist_model.options = set((1, 2))

        with self.assertRaises(APIError):
            # dict
            sellist_model.options = {}

        with self.assertRaises(APIError):
            # tuple
            sellist_model.options = (1,)

    def test_fail_to_set_options_on_instance(self):
        """Test settings options on a property instance, only models are allowed options to be set"""
        sellist_model = self.project.model('Model')
        sellist_part_instance = self.project.parts(model=sellist_model)
        sellist_part_instance = sellist_part_instance[0]
        self.assertEqual(sellist_part_instance.category ,'INSTANCE')

        sellist_property = sellist_part_instance.property('a_select_list_property')
        self.assertTrue(hasattr(sellist_property, 'options'))

        with self.assertRaises(APIError):
            sellist_property.options = [1, 3.14]

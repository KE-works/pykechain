from tests.classes import TestBetamax


class TestSelectListProperty(TestBetamax):
    """Tests for the select list properties"""

    def test_get_options_list(self):
        sellist_model = self.project.model('a_select_list_property')
        assert hasattr(sellist_model, 'options')
        assert isinstance(sellist_model.options, list)
        for item in sellist_model.options:
            assert isinstance(item, str)

    def test_set_options_list(self):
        #setup
        sellist_model = self.project.model('a_select_list_property')
        saved_options_list = [str(i) for i in sellist_model.options]

        #do test
        new_options_list = [1,3.14, "a", u"こんにちは"]
        sellist_model.options = new_options_list
        self.assertListEqual(sellist_model.options, new_options_list)

        sellist_model2 = self.project.model('a_select_list_property')
        self.assertListEqual(sellist_model.options, sellist_model2.optiosn)

        #teardown
        sellist_model.options = saved_options_list

    def test_illegal_options_are_not_set(self):
        sellist_model = self.project.model('a_select_list_property')
        with AssertionError:
            sellist_model.options = 1

        with AssertionError:
            sellist_model.options = None

        with AssertionError:
            sellist_model.options = set([1])

        with AssertionError:
            sellist_model.options = {}




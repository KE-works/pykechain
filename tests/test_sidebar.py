from pykechain.enums import SubprocessDisplayMode, KEChainPages
from pykechain.models.sidebar.sidebar_button import SideBarButton
from pykechain.models.sidebar.sidebar_manager import SideBarManager
from tests.classes import TestBetamax


class TestSideBar(TestBetamax):

    def setUp(self):
        super(TestSideBar, self).setUp()

        self.scope = self.project.clone(asynchronous=False)
        self.manager = SideBarManager(scope=self.scope)
        self.scope_uri = '#/scopes/{}'.format(self.scope.id)
        self.scope_activity_uri = '{}/{}'.format(self.scope_uri, SubprocessDisplayMode.ACTIVITIES)

        self.default_button_config = {
            'title': 'new button',
            'icon': 'bookmark',
            'uri': '{}/{}'.format(self.scope_uri, KEChainPages.DATA_MODEL)
        }

    def tearDown(self):
        self.scope.delete()
        super(TestSideBar, self).tearDown()

    def test_manager(self):
        side_bar_manager = SideBarManager(scope=self.scope)

        self.assertIsInstance(side_bar_manager, SideBarManager)

    def test_create_button(self):
        new_button = self.manager.create_button(**self.default_button_config)

        self.assertIsInstance(new_button, SideBarButton)
        self.assertTrue(new_button is self.manager[-1])

    def test_delete_button(self):
        new_button = self.manager.create_button(**self.default_button_config)
        new_button.delete()

        self.assertNotIn(new_button, self.manager)

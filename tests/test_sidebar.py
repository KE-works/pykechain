from pykechain.enums import SubprocessDisplayMode, KEChainPages
from pykechain.models import Scope2
from pykechain.models.sidebar.sidebar_button import SideBarButton
from pykechain.models.sidebar.sidebar_manager import SideBarManager
from tests.classes import TestBetamax


class TestSideBar(TestBetamax):

    def setUp(self):
        super(TestSideBar, self).setUp()

        self.scope = self.project.clone(asynchronous=False)  # type: Scope2
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

    def test_singleton_manager_per_scope(self):
        manager_1 = SideBarManager(scope=self.scope)
        manager_2 = self.scope.side_bar()

        self.assertTrue(manager_1 is manager_2,
                        msg='There are 2 different manager objects while the same object is expected.')

    def test_create_button(self):
        new_button = self.manager.create_button(**self.default_button_config)

        self.assertIsInstance(new_button, SideBarButton)
        self.assertTrue(new_button is self.manager[-1])

    def test_delete_button(self):
        new_button = self.manager.create_button(**self.default_button_config)
        new_button.delete()

        self.assertNotIn(new_button, self.manager)

    def test_add_buttons(self):
        buttons = [
            {
                'displayName': 'activity button',
                'displayIcon': 'bookmark',
                'uri': '{}/{}'.format(self.scope_activity_uri, self.scope.activities()[0].id),
            },
            {
                'displayName': 'ke-chain page',
                'displayIcon': 'university',
                'uri': '{}/{}'.format(self.scope_uri, KEChainPages.EXPLORER)
            },
            {
                'displayName': 'external button',
                'displayIcon': 'google',
                'uri': 'https://www.google.com',
            },
        ]
        new_buttons = self.manager.add_buttons(
            buttons=buttons,
            override_sidebar=True,
        )

        self.assertIsInstance(new_buttons, list)
        self.assertTrue(all(isinstance(b, SideBarButton) for b in new_buttons))
        self.assertTrue(len(self.manager) == 3)

    def test_bulk_creation(self):
        bulk_creation_manager = SideBarManager(scope=self.scope, bulk_creation=True)
        bulk_creation_manager.add_task_button(
            activity=self.scope.activities()[0],
            icon='bookmark',
        )
        bulk_creation_manager.add_external_button(
            url='https://www.google.com',
            icon='google',
            title='Google',
        )
        bulk_creation_manager.add_ke_chain_page(
            page_name=KEChainPages.WORK_BREAKDOWN,
            icon='site-map'
        )

        self.assertNotIn('customNavigation', self.scope.options,
                         msg='During bulk creation of buttons, KE-chain should not be updated yet.')

        bulk_creation_manager.__del__()  # deleting the manager updates KE-chain

        self.assertIn('customNavigation', self.scope.options)

        updated_side_bar_buttons = self.scope.options.get('customNavigation')
        self.assertTrue(len(updated_side_bar_buttons) == 3,
                        msg='At the end of bulk creation, the buttons must have been created.')

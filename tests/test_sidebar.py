from pykechain.enums import SubprocessDisplayMode, KEChainPages, ScopeStatus
from pykechain.exceptions import IllegalArgumentError, NotFoundError
from pykechain.models import Scope
from pykechain.models.sidebar.sidebar_button import SideBarButton
from pykechain.models.sidebar.sidebar_manager import SideBarManager
from tests.classes import TestBetamax


class TestSideBar(TestBetamax):

    def setUp(self):
        super(TestSideBar, self).setUp()

        self.scope = self.project.clone(asynchronous=False)  # type: Scope
        del self.project

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

    def test_loading_of_existing_buttons(self):
        for scope in self.client.scopes(status=ScopeStatus.ACTIVE):
            scope.side_bar()

    def test_override_sidebar_property(self):
        value = self.manager.override_sidebar

        self.assertIsInstance(value, bool)
        self.assertFalse(value)

        self.manager.override_sidebar = True

        self.assertTrue(self.manager.override_sidebar)

    def test_create_button(self):
        new_button = self.manager.create_button(**self.default_button_config)

        self.assertIsInstance(new_button, SideBarButton)
        self.assertTrue(new_button is self.manager[-1])
        self.assertIsInstance(new_button.__repr__(), str)

    # noinspection PyTypeChecker
    def test_create_button_incorrect_arguments(self):
        with self.assertRaises(IllegalArgumentError):
            SideBarButton(self.manager, order='3')

        with self.assertRaises(IllegalArgumentError):
            SideBarButton(self.manager, order=1, title=False)

        with self.assertRaises(IllegalArgumentError):
            SideBarButton(self.manager, order=1, title='Button', icon=32)

        with self.assertRaises(IllegalArgumentError):
            SideBarButton(self.manager, order=1, title='Button', icon='pennant', uri=44)

        with self.assertRaises(IllegalArgumentError):
            SideBarButton(self.manager, order=1, title='Button', icon='pennant', uri='http://www.google.com',
                          uri_target='any')

        with self.assertRaises(IllegalArgumentError):
            SideBarButton(self.manager, order=1, title='Button', icon='pennant', uri='http://www.google.com',
                          icon_mode='best')

        with self.assertRaises(IllegalArgumentError):
            SideBarButton(self.manager, order=1, title='Button', icon='pennant', uri='http://www.google.com',
                          random='unsupported keyword')

    def test_edit_button(self):
        custom_name = "Custom Dutch name"
        new_button = self.manager.create_button(**self.default_button_config)

        new_button.edit(
            display_icon="pennant",
            displayName_nl=custom_name,
        )
        new_button.refresh()

        self.assertEqual("pennant", new_button.display_icon)
        self.assertEqual(custom_name, new_button._other_attributes.get("displayName_nl"))

    def test_delete_button(self):
        new_button = self.manager.create_button(**self.default_button_config)
        new_button.delete()

        self.assertNotIn(new_button, self.manager)

    def test_get_button(self):
        new_button = self.manager.create_button(**self.default_button_config)

        button_from_index = self.manager[0]
        button_from_title = self.manager['new button']
        button_from_button = self.manager[new_button]

        self.assertIs(new_button, button_from_index)
        self.assertIs(new_button, button_from_title)
        self.assertIs(new_button, button_from_button)

        with self.assertRaises(IndexError):
            # noinspection PyStatementEffect
            self.manager[3]

        with self.assertRaises(NotFoundError):
            # noinspection PyStatementEffect
            self.manager['unused button title']

    def test_remove_button(self):
        new_button = self.manager.create_button(**self.default_button_config)

        self.manager.remove(new_button)

        self.assertTrue(len(self.manager) == 0)

    def test_insert_button(self):
        button_1 = self.manager.create_button(order=0, **self.default_button_config)
        button_2 = self.manager.create_button(order=1, **self.default_button_config)
        button_3 = self.manager.create_button(order=2, **self.default_button_config)

        self.manager.insert(0, button_2)

        self.assertListEqual(
            [button_2, button_1, button_3],
            list(self.manager),
        )

    def test_bulk_add_buttons(self):
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

    def test_context_manager(self):
        with SideBarManager(scope=self.scope) as bulk_creation_manager:

            bulk_creation_manager.override_sidebar = True

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
                icon='sitemap',
            )

            self.assertEqual(0, len(self.scope.options['customNavigation']),
                             msg='During bulk creation of buttons, KE-chain should not be updated yet.')

        self.assertEqual(3, len(self.scope.options['customNavigation']),
                         msg='After closing the context `with`, update should be performed.')

        updated_side_bar_buttons = self.scope.options.get('customNavigation')
        self.assertTrue(len(updated_side_bar_buttons) == 3,
                        msg='At the end of bulk creation, the buttons must have been created.')

        self.assertTrue(self.scope.options.get('overrideSideBar'))

    def test_load_buttons(self):
        # setup: create a custom button
        with self.scope.side_bar() as sbm:
            sbm.override_sidebar = True
            sbm.add_ke_chain_page(KEChainPages.WORK_BREAKDOWN)

        # Reload side-bar from KE-chain
        self.scope.side_bar().refresh()

        # testing: delete original button (this tests the "load") and add another one
        with self.scope.side_bar() as sbm:
            for button in sbm:
                sbm.delete_button(button)
            sbm.override_sidebar = True
            sbm.add_ke_chain_page(KEChainPages.TASKS)

        self.assertEqual(1, len(self.scope.options.get('customNavigation')))

    def test_attributes_button(self):
        display_name_nl = "Het data model"
        button_title = "New button"

        # Check whether all attributes are retrieved and set
        with self.scope.side_bar() as sbm:
            sbm.add_ke_chain_page(
                page_name=KEChainPages.DATA_MODEL,
                title=button_title,
                displayName_nl=display_name_nl,
            )

        # Reload side-bar from KE-chain
        self.scope.side_bar().refresh()

        sbm = self.scope.side_bar()
        found = False
        for button in sbm:  # type: SideBarButton
            if button._other_attributes.get("displayName_nl") == display_name_nl:
                found = True

        self.assertTrue(found)

    def test_attributes_sidebar(self):
        sbm = self.scope.side_bar()

        # Check starting condition
        self.assertFalse(sbm.override_sidebar)

        # Set value
        sbm.override_sidebar = True

        # Reload side-bar from KE-chain
        sbm.refresh()

        # Test attributes
        self.assertTrue(sbm.override_sidebar)

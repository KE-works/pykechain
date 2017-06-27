import json
import uuid

from jsonschema import ValidationError

from pykechain.enums import ComponentXType
from pykechain.exceptions import InspectorComponentError
from pykechain.models.inspector_base import Customization
from pykechain.models.inspectors import SuperGrid, PropertyGrid, PaginatedGrid, FilteredGrid, HtmlPanel
from tests.classes import TestBetamax


class TestWidgetConfig(TestBetamax):
    def setUp(self):
        super(TestWidgetConfig, self).setUp()
        self.parent = self.project.part('Bike')
        self.activity = self.project.activity('Customized task')
        self.model = self.project.model('Wheel')
        self.viewModel = {
            'data': {
                'actions': {
                    'export': True,
                    'newInstance': True,
                    'edit': True,
                    'delete': True
                }
            }
        }
        self.html = "<h1><a href=https://kec2api.ke-chain.com/#scopes/6f7bc9f0-228e-4d3a-9dc0-ec5a75d73e1d/productmodel target=_blank>Link to Data Model</a></h1>"

    def test_single_widget_config(self):
        config_str = "{\n   \"components\":[\n      {\n         \"xtype\":\"superGrid\",\n         \"filter\":{\n            \"parent\":\"e334fa50-9ce9-46ca-b8dc-97a0018f33a4\",\n            \"model\":\"4c0e22e5-3890-4763-873e-937f24c7732e\",\n\"activity_id\" : \"7a41b32c-c02c-483a-81be-beaadc51d534\"\n         },\n         \"viewModel\":{\n            \"data\": {\n                \"actions\":{\n                    \"newInstance\": false,\n                    \"edit\": true,\n                    \"delete\": false,\n                    \"export\": true\n                } \n            }\n        \n        }\n      }\n   ]\n}"
        customisation = Customization(json.loads(config_str))
        customisation.validate()
        self.assertEqual(len(customisation.components), 1)

    def test_multiple_widget_config(self):
        config_str = "{\n   \"components\":[\n      {\n         \"xtype\":\"superGrid\",\n         \"filter\":{\n            \"parent\":\"91d0b3f3-ea42-4b8e-8e71-821f0407ab30\",\n            \"model\":\"7f03ab2c-f7c1-441a-95ad-2ea5adb0f890\",\n\"activity_id\":\"5d569790-1434-49ea-8c50-7107da22b6e8\"\n         },\n         \"viewModel\":{\n            \"data\": {\n                \"actions\":{\n                    \"newInstance\": true,\n                    \"edit\": true,\n                    \"delete\": false,\n                    \"export\": true\n                } \n            }\n        \n        }\n      } , {\n         \"xtype\":\"superGrid\",\n         \"filter\":{\n            \"parent\":\"b0891403-e8e0-48f6-859f-dc3278533dc9\",\n            \"model\":\"27dc444c-7aab-4b3c-b64a-a35546f049a3\",\n\"activity_id\":\"5d569790-1434-49ea-8c50-7107da22b6e8\"\n         },\n         \"viewModel\":{\n            \"data\": {\n                \"actions\":{\n                    \"newInstance\": false,\n                    \"edit\": true,\n                    \"delete\": false,\n                    \"export\": true\n                } \n            }\n        \n        }\n      },  {\n         \"xtype\":\"superGrid\",\n         \"filter\":{\n            \"parent\":\"e334fa50-9ce9-46ca-b8dc-97a0018f33a4\",\n            \"model\":\"4c0e22e5-3890-4763-873e-937f24c7732e\",\n\"activity_id\":\"5d569790-1434-49ea-8c50-7107da22b6e8\"\n         },\n         \"viewModel\":{\n            \"data\": {\n                \"actions\":{\n                    \"newInstance\": false,\n                    \"edit\": true,\n                    \"delete\": false,\n                    \"export\": true\n                } \n            }\n        \n        }\n      }, {\n         \"xtype\":\"superGrid\",\n         \"filter\":{\n            \"parent\":\"296bbdbb-2e45-419d-a223-7ba147fc555e\",\n            \"model\":\"523d30d5-fc82-42d3-b9cb-2a181d4c15a3\",\n\"activity_id\":\"5d569790-1434-49ea-8c50-7107da22b6e8\"\n         },\n         \"viewModel\":{\n            \"data\": {\n                \"actions\":{\n                    \"newInstance\": false,\n                    \"edit\": true,\n                    \"delete\": false,\n                    \"export\": true\n                } \n            }\n        \n        }\n      }, {\n         \"xtype\":\"superGrid\",\n         \"filter\":{\n            \"parent\":\"e9db77e7-8d5b-48e3-9775-aabcedd94399\",\n            \"model\":\"cc5f5bad-40bf-4fdf-bacb-181653ac49f2\",\n\"activity_id\":\"5d569790-1434-49ea-8c50-7107da22b6e8\"\n         },\n         \"viewModel\":{\n            \"data\": {\n                \"actions\":{\n                    \"newInstance\": false,\n                    \"edit\": true,\n                    \"delete\": false,\n                    \"export\": true\n                } \n            }\n        \n        \n      } \n      }\n   ]\n}"
        customisation = Customization(json.loads(config_str))
        customisation.validate()
        self.assertEqual(len(customisation.components), 5)

    def test_invalid_json_widget_config(self):
        config_str = "{\n   \"components\":[\n   {\n         \"xtype\":\"propertyGrid\",\n         \"filter\":{\n            \"part\":\t\"dab86a6b-4136-4433-a850-041ef01653e1\"\n         },\n \"viewModel\":{\n                \"data\": { \n                 \"style\": { \"displayPartTitle\": true } \n            }\n        }\n      \n        },\n      {\n         \"xtype\":\"propertyGrid\",\n         \"filter\":{\n            \"part\":\"66d68d9a-c114-4062-8086-89a1fd3413c8\"\n         },\n      \n        }\n]\n}"
        with self.assertRaises(ValueError):
            # got Expecting property name enclosed in double quotes: line 21 column 9 (char 435)
            customisation = Customization(json=json.loads(config_str))

    def test_invalid_uuid_in_widget_config(self):
        config_str = "{\n   \"components\":[\n\n {\n         \"xtype\":\"propertyGrid\",\n         \"filter\":{\n            \"part\":\"2121914f-cafd-4c6c-8c4f-2b6a365d7c8d\"\n         },\n         \"viewModel\":{\n                \"data\": { \n                 \"style\": { \"displayPartTitle\": true } \n            }\n        }\n      },\n\n      {\n         \"xtype\":\"propertyGrid\",\n         \"filter\":{\n            \"part\":\"c6230290-0515-4575-9dc8-9399e712960b\"\n         },\n         \"viewModel\":{\n                \"data\": { \n                 \"style\": { \"displayPartTitle\": true } \n            }\n        }\n      },\n\n\n      {\n         \"xtype\":\"propertyGrid\",\n         \"filter\":{\n            \"part\":\" 8395b4a6-186b-4215-8168-6574e65a1571\"\n         },\n         \"viewModel\":{\n                \"data\": { \n                 \"style\": { \"displayPartTitle\": true } \n            }\n        }\n      },\n\n\n      {\n         \"xtype\":\"propertyGrid\",\n         \"filter\":{\n            \"part\":\"a90c2d7b-c496-4bdf-85c7-af6685fff9e8\"\n         },\n         \"viewModel\":{\n                \"data\": { \n                 \"style\": { \"displayPartTitle\": true } \n            }\n        }\n      },\n\n {\n         \"xtype\":\"propertyGrid\",\n         \"filter\":{\n            \"part\":\"0ce033e7-640d-4307-b125-b5f013df29b2\"\n         },\n         \"viewModel\":{\n                \"data\": { \n                 \"style\": { \"displayPartTitle\": true } \n            }\n        }\n      }\n\n\n\n\n   ]\n}"
        with self.assertRaises(ValidationError):
            # got ' 8395b4a6-186b-4215-8168-6574e65a1571' does not match '^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$'
            #
            # Failed validating 'pattern' in schema['properties']['filter']['properties']['part']:
            #     {'pattern': '^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$',
            #      'type': 'string'}
            #
            # On instance['filter']['part']:
            #     ' 8395b4a6-186b-4215-8168-6574e65a1571'
            customisation = Customization(json.loads(config_str))
            customisation.validate()

    def test_empty_component_fails_with_validation_error(self):
        with self.assertRaises(InspectorComponentError):
            SuperGrid()
        with self.assertRaises(InspectorComponentError):
            PropertyGrid()
        with self.assertRaises(InspectorComponentError):
            PaginatedGrid()
        with self.assertRaises(InspectorComponentError):
            FilteredGrid()
        with self.assertRaises(InspectorComponentError):
            HtmlPanel()

    def test_supergrid_component(self):
        component = SuperGrid(parent=str(uuid.uuid4()), model=str(uuid.uuid4()), activity_id=str(uuid.uuid4()),
                              title="a title")
        component.validate()

        component = SuperGrid(parent=str(uuid.uuid4()), model=str(uuid.uuid4()), activity_id=str(uuid.uuid4()),
                              title="a title", newInstance=False, edit=False, delete=False, export=False)
        component.validate()

    def test_propertygrid_component_no_title(self):
        component = PropertyGrid(part=str(uuid.uuid4()))
        component.validate()

    def test_propertygrid_component_with_title(self):
        component = PropertyGrid(part=str(uuid.uuid4()), title="some title")
        component.validate()

    def test_filteredgrid_component(self):
        component = FilteredGrid(parent=str(uuid.uuid4), model=str(uuid.uuid4()))
        component.validate()

    def test_paginatedgrid_component_no_title(self):
        component = PaginatedGrid(model=str(uuid.uuid4()), parent=str(uuid.uuid4()))
        component.validate()

    def test_paginatedgrid_component_with_title_and_extras(self):
        component = PaginatedGrid(model=str(uuid.uuid4()), parent=str(uuid.uuid4()), title="a title")
        component.validate()

        component = PaginatedGrid(model=str(uuid.uuid4()), parent=str(uuid.uuid4()), title="a title",
                                  newInstance=False, edit=False, delete=False, export=False)
        component.validate()

    def test_supergrid_with_part_objects_and_json(self):
        # Set up
        title = "Customized SuperGrid"
        json_config = {'xtype': ComponentXType.SUPERGRID,
                       'filter': {'activity_id': self.activity.id, 'model': self.model.id, 'parent': self.parent.id},
                       'title': title,
                       'viewModel': self.viewModel
                       }

        # First customization - using parent, model and activity
        first_component = SuperGrid(parent=self.parent, model=self.model, activity_id=self.activity, title=title)
        first_customization = Customization()
        first_customization.add_component(first_component)
        self.activity.customize(first_customization.as_dict())
        config_first_customization = self.activity._json_data['widget_config']['config']

        # Second customization - using json only
        second_component = SuperGrid(json=json_config)
        second_customization = Customization()
        second_customization.add_component(second_component)
        self.activity.customize(second_customization.as_dict())
        config_second_customization = self.activity._json_data['widget_config']['config']

        # Check whether the configs are equal
        self.assertEqual(json.loads(config_first_customization), json.loads(config_second_customization))

        # teardown
        self.activity.customize(config={})

    def test_propertygrid_with_part_objects_and_json(self):
        # Set up
        title = "Customized PropertyGrid"
        json_config = {'xtype': ComponentXType.PROPERTYGRID,
                       'filter': {'part': self.parent.id},
                       'title': title,
                       'viewModel': {
                           'data': {
                               'style': {
                                   'displayPartTitle': True
                               }
                           }
                       }
                       }

        # First customization - using part instance only
        first_component = PropertyGrid(part=self.parent, title=title)
        first_customization = Customization()
        first_customization.add_component(first_component)
        self.activity.customize(first_customization.as_dict())
        config_first_customization = self.activity._json_data['widget_config']['config']

        # Second customization - using json only
        second_component = PropertyGrid(json=json_config)
        second_customization = Customization()
        second_customization.add_component(second_component)
        self.activity.customize(second_customization.as_dict())
        config_second_customization = self.activity._json_data['widget_config']['config']

        # Check whether the configs are equal
        self.assertEqual(json.loads(config_first_customization), json.loads(config_second_customization))

        # teardown
        self.activity.customize(config={})

    def test_paginatedsupergrid_with_part_objects_and_json(self):
        # Set up
        title = "Customized PaginatedGrid"
        json_config = {'xtype': ComponentXType.PAGINATEDSUPERGRID,
                       'filter': {'model': self.model.id, 'parent': self.parent.id},
                       'title': title,
                       'pageSize': 25,
                       'flex': 0,
                       'height': 600,
                       'viewModel': self.viewModel
                       }

        # First customization - using parent and model
        first_component = PaginatedGrid(parent=self.parent, model=self.model, title=title)
        first_customization = Customization()
        first_customization.add_component(first_component)
        self.activity.customize(first_customization.as_dict())
        config_first_customization = self.activity._json_data['widget_config']['config']

        # Second customization - using only json
        second_component = PaginatedGrid(json=json_config)
        second_customization = Customization()
        second_customization.add_component(second_component)
        self.activity.customize(second_customization.as_dict())
        config_second_customization = self.activity._json_data['widget_config']['config']

        # Check whether the configs are equal
        self.assertEqual(json.loads(config_first_customization), json.loads(config_second_customization))

        # teardown
        self.activity.customize(config={})

    def test_filteredgrid_with_part_objects_and_json(self):
        # Set up
        title = "Customized FilteredGrid"
        json_config = {'xtype': ComponentXType.FILTEREDGRID,
                       'partModelId': self.model.id,
                       'parentInstanceId': self.parent.id,
                       'title': title,
                       'collapseFilters': False,
                       'pageSize': 25,
                       'flex': 0,
                       'height': 600,
                       'grid': {'xtype': ComponentXType.PAGINATEDSUPERGRID, 'viewModel': self.viewModel}
                       }

        # First customization - using parent and model
        first_component = FilteredGrid(parent=self.parent, model=self.model, title=title)
        first_customization = Customization()
        first_customization.add_component(first_component)
        self.activity.customize(first_customization.as_dict())
        config_first_customization = self.activity._json_data['widget_config']['config']

        # Second customization - using only json
        second_component = FilteredGrid(json=json_config)
        second_customization = Customization()
        second_customization.add_component(second_component)
        self.activity.customize(second_customization.as_dict())
        config_second_customization = self.activity._json_data['widget_config']['config']

        # Check whether the configs are equal
        self.assertEqual(json.loads(config_first_customization), json.loads(config_second_customization))

        # teardown
        self.activity.customize(config={})

    def test_htmlpanel_with_part_objects_and_json(self):
        # Set up
        title = 'Customized HTMLPanel'
        json_config = {"xtype": "panel",
                       "title": title,
                       "html": self.html
                       }

        # First customization - using html
        first_component = HtmlPanel(html=self.html, title=title)
        first_customization = Customization()
        first_customization.add_component(first_component)
        self.activity.customize(first_customization.as_dict())
        config_first_customization = self.activity._json_data['widget_config']['config']

        # Second customization - using only json
        second_component = HtmlPanel(json=json_config)
        second_customization = Customization()
        second_customization.add_component(second_component)
        self.activity.customize(second_customization.as_dict())
        config_second_customization = self.activity._json_data['widget_config']['config']

        # Check whether the configs are equal
        self.assertEqual(json.loads(config_first_customization), json.loads(config_second_customization))

        # teardown
        self.activity.customize(config={})

    def test_set_and_get_methods(self):
        # Set up
        title = "Customized SuperGrid"
        frame_model = self.project.model('Frame')

        # Creating superGrid component
        super_grid = SuperGrid(parent=self.parent, model=self.model, activity_id=self.activity, title=title)

        # Setting the value of model
        super_grid.set('model', frame_model)

        self.assertEqual(frame_model.id, super_grid.get('model'))

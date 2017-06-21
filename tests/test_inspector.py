import json
from unittest import TestCase

from jsonschema import ValidationError

from pykechain.models.inspector_base import Customization


class TestWidgetConfig(TestCase):


    def test_single_widget_config(self):
        config_str = "{\n   \"components\":[\n      {\n         \"xtype\":\"superGrid\",\n         \"filter\":{\n            \"parent\":\"e334fa50-9ce9-46ca-b8dc-97a0018f33a4\",\n            \"model\":\"4c0e22e5-3890-4763-873e-937f24c7732e\",\n\"activity_id\" : \"7a41b32c-c02c-483a-81be-beaadc51d534\"\n         },\n         \"viewModel\":{\n            \"data\": {\n                \"actions\":{\n                    \"newInstance\": false,\n                    \"edit\": true,\n                    \"delete\": false,\n                    \"export\": true\n                } \n            }\n        \n        }\n      }\n   ]\n}"
        customisation = Customization(json.loads(config_str))
        customisation.validate()
        self.assertEqual(len(customisation.components),1)

    def test_multiple_widget_config(self):
        config_str = "{\n   \"components\":[\n      {\n         \"xtype\":\"superGrid\",\n         \"filter\":{\n            \"parent\":\"91d0b3f3-ea42-4b8e-8e71-821f0407ab30\",\n            \"model\":\"7f03ab2c-f7c1-441a-95ad-2ea5adb0f890\",\n\"activity_id\":\"5d569790-1434-49ea-8c50-7107da22b6e8\"\n         },\n         \"viewModel\":{\n            \"data\": {\n                \"actions\":{\n                    \"newInstance\": true,\n                    \"edit\": true,\n                    \"delete\": false,\n                    \"export\": true\n                } \n            }\n        \n        }\n      } , {\n         \"xtype\":\"superGrid\",\n         \"filter\":{\n            \"parent\":\"b0891403-e8e0-48f6-859f-dc3278533dc9\",\n            \"model\":\"27dc444c-7aab-4b3c-b64a-a35546f049a3\",\n\"activity_id\":\"5d569790-1434-49ea-8c50-7107da22b6e8\"\n         },\n         \"viewModel\":{\n            \"data\": {\n                \"actions\":{\n                    \"newInstance\": false,\n                    \"edit\": true,\n                    \"delete\": false,\n                    \"export\": true\n                } \n            }\n        \n        }\n      },  {\n         \"xtype\":\"superGrid\",\n         \"filter\":{\n            \"parent\":\"e334fa50-9ce9-46ca-b8dc-97a0018f33a4\",\n            \"model\":\"4c0e22e5-3890-4763-873e-937f24c7732e\",\n\"activity_id\":\"5d569790-1434-49ea-8c50-7107da22b6e8\"\n         },\n         \"viewModel\":{\n            \"data\": {\n                \"actions\":{\n                    \"newInstance\": false,\n                    \"edit\": true,\n                    \"delete\": false,\n                    \"export\": true\n                } \n            }\n        \n        }\n      }, {\n         \"xtype\":\"superGrid\",\n         \"filter\":{\n            \"parent\":\"296bbdbb-2e45-419d-a223-7ba147fc555e\",\n            \"model\":\"523d30d5-fc82-42d3-b9cb-2a181d4c15a3\",\n\"activity_id\":\"5d569790-1434-49ea-8c50-7107da22b6e8\"\n         },\n         \"viewModel\":{\n            \"data\": {\n                \"actions\":{\n                    \"newInstance\": false,\n                    \"edit\": true,\n                    \"delete\": false,\n                    \"export\": true\n                } \n            }\n        \n        }\n      }, {\n         \"xtype\":\"superGrid\",\n         \"filter\":{\n            \"parent\":\"e9db77e7-8d5b-48e3-9775-aabcedd94399\",\n            \"model\":\"cc5f5bad-40bf-4fdf-bacb-181653ac49f2\",\n\"activity_id\":\"5d569790-1434-49ea-8c50-7107da22b6e8\"\n         },\n         \"viewModel\":{\n            \"data\": {\n                \"actions\":{\n                    \"newInstance\": false,\n                    \"edit\": true,\n                    \"delete\": false,\n                    \"export\": true\n                } \n            }\n        \n        \n      } \n      }\n   ]\n}"
        customisation = Customization(json.loads(config_str))
        customisation.validate()
        self.assertEqual(len(customisation.components), 5)

    def test_invalid_json_widget_config(self):
        config_str = "{\n   \"components\":[\n   {\n         \"xtype\":\"propertyGrid\",\n         \"filter\":{\n            \"part\":\t\"dab86a6b-4136-4433-a850-041ef01653e1\"\n         },\n \"viewModel\":{\n                \"data\": { \n                 \"style\": { \"displayPartTitle\": true } \n            }\n        }\n      \n        },\n      {\n         \"xtype\":\"propertyGrid\",\n         \"filter\":{\n            \"part\":\"66d68d9a-c114-4062-8086-89a1fd3413c8\"\n         },\n      \n        }\n]\n}"
        with self.assertRaises(ValueError):
            #got Expecting property name enclosed in double quotes: line 21 column 9 (char 435)
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

        # class TestParts(TestBetamax):
    #     def test_retrieve_parts(self):
    #         parts = self.project.parts()
    #
    #         # Check if there are parts
    #         assert len(parts)

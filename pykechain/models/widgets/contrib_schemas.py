#
#
import json
import uuid
from pathlib import Path

from jsonschema import validate, Draft6Validator

from pykechain import get_project
from pykechain.enums import WidgetCompatibleTypes, WidgetTypes, ActivityType
from pykechain.models.widgets import Widget
from pykechain.models.widgets.widgetset import WidgetSet

widget_names_values = [
    'superGridWidget', 'propertyGridWidget', 'htmlWidget', 'filteredGridWidget', 'serviceWidget', 'notebookWidget',
    'attachmentViewerWidget', 'taskNavigationBarWidget', 'jsonWidget', 'metaPanelWidget', 'multiColumnWidget'
]

attachment_widget_jsonschema = {
    "$schema": "http://json-schema.org/schema#",
    "title": "Attachment Widget JSON Schema",
    "type": "object",
    "additionalProperties": False,
    "properties": {}
}

widget_jsonschema = {
    "type": "object",
    "properties": {
        "meta": {
            "type": "object"
        },
        "name": {
            "type": "string",
            "enum": widget_names_values
        },
        "config": {"type": "object"},
        "id": "#/definitions/nullString"
    }
}

widgets_jsonschema = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "type": "array",
    "items": {
        "type": "object",
        "properties": {
            "meta": {
                "type": "object"
            },
            "name": {
                "type": "string",
                "enum": widget_names_values
            },
            "config": {"type": "object"},
            "id": {"$ref": "#/definitions/nullString"},
        },
        "required": ["name", "meta"],
        "allOf": [
            {
                "if": {"properties": {"name": {"const": "attachmentViewerWidget"}}},
                "then": {
                    "properties": {
                        "meta": {
                            "type": "object",
                            "properties": {
                                "propertyInstanceId": {"$ref": "#/definitions/uuidString"},
                                "activityId": {"$ref": "#/definitions/uuidString"},
                                "showTitleValue": {"$ref": "#/definitions/nullString"},
                                "customTitle": {"$ref": "#/definitions/nullString"},
                                "noPadding": {"$ref": "#/definitions/nullString"},
                                "customHeight": {"$ref": "#/definitions/positiveInteger"}
                            },
                            "additionalProperties": False,
                            "required": ["propertyInstanceId", "activityId"]
                        }
                    }
                }
            },
            {
                "if": {"properties": {"name": {"const": "htmlWidget"}}},
                "then": {
                    "properties": {
                        "meta": {
                            "type": "object",
                            "properties": {
                                "showTitleValue": {"$ref": "#/definitions/nullString"},
                                "customTitle": {"$ref": "#/definitions/nullString"},
                                "noPadding": {"$ref": "#/definitions/nullString"},
                                "customHeight": {"$ref": "#/definitions/positiveInteger"},
                                "collapsed": {"$ref": "#/definitions/booleanNull"},
                                "collapsible": {"$ref": "#/definitions/booleanNull"},
                                "html": {"type": "string"}
                            },
                            "additionalProperties": False,
                            "required": ["html"]
                        }
                    }
                }
            }
        ]
    },
    "definitions": {
        "uuidString": {"type": "string",
                       "pattern": "^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$"},
        "nullString": {"type": ["string", "null"]},
        "positiveInteger": {"type": "integer", "minimum": 0},
        "booleanNull": {"type": ["boolean", "null"]}
        # "singleWidget": widget_jsonschema,

        # "widget": {
        #     "base": widget_jsonschema,
        #     "attachmentViewerWidget": {
        #         "$ref": "#/definitions/widget/base",
        #         "name":"attachmentViewerWidget",
        #         "properties": {
        #             "name": "attachmentViewerWidget",
        #             "propertyInstanceId": "#/definitions/uuidString",
        #             "activityId": "#/definitions/uuidString",
        #             "showTitleValue": "#/definitions/nullString",
        #             "customTitle": "#/definitions/nullString",
        #             "noPadding": "#/definitions/nullString"
        #         },
        #         "additionalProperties": False,
        #         "required": ["name", "propertyInstanceId", "activityId"]
        #     }
        # }
    }
}

widgets = [
    {
        "config": {
            "height": 110,
            "xtype": "propertyAttachmentViewer",
            "filter": {
                "activity_id": "4d5c31f0-d57a-4452-a6cc-41483c869e16"
            },
            "showTitleValue": "No title",
            "title": None,
            "propertyId": "ae22ac3f-c52c-4f32-a215-21d2775e7cd1"
        },
        "name": "attachmentViewerWidget",
        "meta": {
            "customTitle": None,
            "activityId": "4d5c31f0-d57a-4452-a6cc-41483c869e16",
            "customHeight": 110,
            "propertyInstanceId": "ae22ac3f-c52c-4f32-a215-21d2775e7cd1",
            "showTitleValue": "No title"
        }
    },
    {
        "config": {
            "xtype": "activityNavigationBar",
            "alignment": "center",
            "filter": {
                "activity_id": "4d5c31f0-d57a-4452-a6cc-41483c869e16"
            },
            "taskButtons": [
                {
                    "activityId": "4d5c31f0-d57a-4452-a6cc-41483c869e16",
                    "emphasize": False,
                    "customText": ""
                },
                {
                    "customText": "",
                    "activityId": "931c82dc-2464-448c-88ab-311794201856",
                    "emphasize": False,
                    "disabled": False
                },
                {
                    "customText": "",
                    "activityId": "8e46caaa-29db-4dcd-a19a-ffc923412761",
                    "emphasize": False,
                    "disabled": False
                },
                {
                    "customText": "",
                    "activityId": "1934371b-35ac-4618-aec5-acd471f8d92b",
                    "emphasize": False,
                    "disabled": False
                },
                {
                    "customText": "",
                    "activityId": "41d5a106-b580-4faf-9ef3-70eb67f25611",
                    "emphasize": False,
                    "disabled": False
                }
            ]
        },
        "name": "taskNavigationBarWidget",
        "meta": {
            "activityId": "4d5c31f0-d57a-4452-a6cc-41483c869e16",
            "alignment": "center",
            "taskButtons": [
                {
                    "activityId": "4d5c31f0-d57a-4452-a6cc-41483c869e16",
                    "name": "Start calculation",
                    "emphasize": False,
                    "customText": ""
                },
                {
                    "isDisabled": False,
                    "activityId": "931c82dc-2464-448c-88ab-311794201856",
                    "name": "Specify vehicle data",
                    "emphasize": False,
                    "customText": ""
                },
                {
                    "isDisabled": False,
                    "activityId": "8e46caaa-29db-4dcd-a19a-ffc923412761",
                    "name": "Brake system overview",
                    "emphasize": False,
                    "customText": ""
                },
                {
                    "isDisabled": False,
                    "activityId": "1934371b-35ac-4618-aec5-acd471f8d92b",
                    "name": "Result overview",
                    "emphasize": False,
                    "customText": ""
                },
                {
                    "isDisabled": False,
                    "activityId": "41d5a106-b580-4faf-9ef3-70eb67f25611",
                    "name": "Print report",
                    "emphasize": False,
                    "customText": ""
                }
            ]
        }
    },
    {
        "config": {
            "title": "Instructions",
            "xtype": "htmlPanel",
            "collapsed": True,
            "collapsible": True,
            "html": "<span style=\"font-family: Arial; white-space: pre-wrap;\">Please provide the following details and operational requirements for the brake calculation of your vehicle.</span>"
        },
        "name": "htmlWidget",
        "meta": {
            "customTitle": "Instructions",
            "showTitleValue": "Custom title",
            "collapsed": True,
            "collapsible": True,
            "html": "<span style=\"font-family: Arial; white-space: pre-wrap;\">Please provide the following details and operational requirements for the brake calculation of your vehicle.</span>"
        }
    },
    {
        "config": {
            "height": None,
            "xtype": "propertyGrid",
            "collapsible": True,
            "filter": {
                "activity_id": "4d5c31f0-d57a-4452-a6cc-41483c869e16",
                "part": "7241ccfa-3a89-4114-b60a-202c9dac9f7e"
            },
            "hideHeaders": True,
            "title": "Settings",
            "showTitleValue": "Custom title",
            "category": "instance",
            "collapsed": True,
            "viewModel": {
                "data": {
                    "displayColumns": {
                        "unit": False,
                        "description": False
                    }
                }
            }
        },
        "name": "propertyGridWidget",
        "meta": {
            "showHeaders": False,
            "activityId": "4d5c31f0-d57a-4452-a6cc-41483c869e16",
            "showColumns": [],
            "collapsible": True,
            "showTitleValue": "Custom title",
            "customTitle": "Settings",
            "partInstanceId": "7241ccfa-3a89-4114-b60a-202c9dac9f7e",
            "collapsed": True,
            "customHeight": None,
            "showHeightValue": "Automatic height"
        }
    },
    {
        "config": {
            "title": "Trailer details"
        },
        "id": "mc1",
        "name": "multiColumnWidget",
        "meta": {
            "height": 184,
            "customTitle": "Trailer details",
            "collapsed": False,
            "collapsible": False,
            "showTitleValue": "Custom title"
        }
    },
    {
        "config": {
            "height": None,
            "xtype": "propertyGrid",
            "filter": {
                "activity_id": "4d5c31f0-d57a-4452-a6cc-41483c869e16",
                "part": "705a1d8e-46e7-4184-a072-51119ef8c321"
            },
            "hideHeaders": True,
            "title": "Column 1",
            "category": "instance",
            "showTitleValue": "Default",
            "viewModel": {
                "data": {
                    "displayColumns": {
                        "unit": False,
                        "description": False
                    }
                }
            }
        },
        "parentId": "mc1",
        "name": "propertyGridWidget",
        "meta": {
            "showHeaders": False,
            "activityId": "4d5c31f0-d57a-4452-a6cc-41483c869e16",
            "showColumns": [],
            "showTitleValue": "No title",
            "customTitle": None,
            "partInstanceId": "705a1d8e-46e7-4184-a072-51119ef8c321",
            "customHeight": None,
            "showHeightValue": "Automatic height"
        }
    },
    {
        "config": {
            "height": None,
            "xtype": "propertyGrid",
            "filter": {
                "activity_id": "4d5c31f0-d57a-4452-a6cc-41483c869e16",
                "part": "0bc0ca12-fe5b-4ca3-b430-f0b39e63cf4d"
            },
            "hideHeaders": True,
            "title": "Column 2",
            "category": "instance",
            "showTitleValue": "Default",
            "viewModel": {
                "data": {
                    "displayColumns": {
                        "unit": False,
                        "description": False
                    }
                }
            }
        },
        "parentId": "mc1",
        "name": "propertyGridWidget",
        "meta": {
            "showHeaders": False,
            "activityId": "4d5c31f0-d57a-4452-a6cc-41483c869e16",
            "showColumns": [],
            "showTitleValue": "No title",
            "partInstanceId": "0bc0ca12-fe5b-4ca3-b430-f0b39e63cf4d",
            "customHeight": None,
            "showHeightValue": "Automatic height"
        }
    },
    {
        "config": {
            "title": "Additional requests"
        },
        "id": "mc2",
        "name": "multiColumnWidget",
        "meta": {
            "height": 60,
            "customTitle": "Additional requests",
            "collapsed": False,
            "collapsible": False,
            "showTitleValue": "Custom title"
        }
    },
    {
        "config": {
            "height": None,
            "xtype": "propertyGrid",
            "filter": {
                "activity_id": "4d5c31f0-d57a-4452-a6cc-41483c869e16",
                "part": "4622e177-643a-411b-aaaa-81b39b8fdafd"
            },
            "hideHeaders": True,
            "title": None,
            "category": "instance",
            "showTitleValue": "No title",
            "viewModel": {
                "data": {
                    "displayColumns": {
                        "unit": False,
                        "description": False
                    }
                }
            }
        },
        "parentId": "mc2",
        "name": "propertyGridWidget",
        "meta": {
            "showHeaders": False,
            "activityId": "4d5c31f0-d57a-4452-a6cc-41483c869e16",
            "showColumns": [],
            "showTitleValue": "No title",
            "customTitle": None,
            "partInstanceId": "4622e177-643a-411b-aaaa-81b39b8fdafd",
            "customHeight": None,
            "showHeightValue": "Automatic height"
        }
    },
    {
        "config": {
            "height": None,
            "xtype": "propertyGrid",
            "filter": {
                "activity_id": "4d5c31f0-d57a-4452-a6cc-41483c869e16",
                "part": "40c8ea99-b2ec-4c28-b89d-df322175c9ae"
            },
            "hideHeaders": True,
            "title": None,
            "category": "instance",
            "showTitleValue": "No title",
            "viewModel": {
                "data": {
                    "displayColumns": {
                        "unit": False,
                        "description": False
                    }
                }
            }
        },
        "parentId": "mc2",
        "name": "propertyGridWidget",
        "meta": {
            "showHeaders": False,
            "activityId": "4d5c31f0-d57a-4452-a6cc-41483c869e16",
            "showColumns": [],
            "showTitleValue": "No title",
            "customTitle": None,
            "partInstanceId": "40c8ea99-b2ec-4c28-b89d-df322175c9ae",
            "customHeight": None,
            "showHeightValue": "Automatic height"
        }
    },
    {
        "config": {
            "xtype": "executeService",
            "showTitleValue": "No title",
            "title": None,
            "customButtonText": "Submit vehicle specification",
            "viewModel": {
                "data": {
                    "canDownloadLog": False,
                    "buttonUI": "primary-action"
                }
            },
            "serviceId": "2b755e56-08c0-4e5b-8b5b-08bd636fcf9e"
        },
        "name": "serviceWidget",
        "meta": {
            "showDownloadLog": False,
            "serviceId": "2b755e56-08c0-4e5b-8b5b-08bd636fcf9e",
            "showTitleValue": "No title",
            "customTitle": None,
            "emphasizeButton": True,
            "customText": "Submit vehicle specification",
            "showButtonValue": "Custom text"
        }
    },
    {
        "config": {
            "title": "Information and warnings",
            "xtype": "htmlPanel",
            "collapsed": False,
            "collapsible": False,
            "html": "<font color=\"#003399\"><div>The regulation required for Type approval is ECE-R13.<br><br>You may now proceed to the \"Specify vehicle data\" page.</div></font>"
        },
        "name": "htmlWidget",
        "meta": {
            "customTitle": "Information and warnings",
            "showTitleValue": "Custom title",
            "collapsed": False,
            "collapsible": False,
            "html": "<font color=\"#003399\"><div>The regulation required for Type approval is ECE-R13.<br><br>You may now proceed to the \"Specify vehicle data\" page.</div></font>"
        }
    },
    {
        "config": {
            "xtype": "activityNavigationBar",
            "alignment": "center",
            "filter": {
                "activity_id": "4d5c31f0-d57a-4452-a6cc-41483c869e16"
            },
            "taskButtons": [
                {
                    "customText": "Proceed to specify vehicle data",
                    "activityId": "931c82dc-2464-448c-88ab-311794201856",
                    "emphasize": True,
                    "disabled": False
                }
            ]
        },
        "name": "taskNavigationBarWidget",
        "meta": {
            "activityId": "4d5c31f0-d57a-4452-a6cc-41483c869e16",
            "alignment": "center",
            "taskButtons": [
                {
                    "isDisabled": False,
                    "activityId": "931c82dc-2464-448c-88ab-311794201856",
                    "name": "Specify vehicle data",
                    "emphasize": True,
                    "customText": "Proceed to Specify vehicle data"
                }
            ]
        }
    }
]

if __name__ == '__main__':
    Draft6Validator.check_schema(widgets_jsonschema)
    validate(widgets, widgets_jsonschema)

    widgets_metas = [{
        "widget_type": WidgetCompatibleTypes.get(w.get('name'), WidgetTypes.UNDEFINED),
        "meta": w.get('meta'),
        "id": uuid.uuid4()
    } for w in widgets]

    print(widgets_metas)
    widgetset = WidgetSet([Widget.create(json=w, client=object()) for w in widgets_metas])
    print(widgetset)

    # project = get_project(env_filename=Path("/home/jochem/dev/pykechain/.env").name)
    # all_activities = project.activities()
    # for activity in all_activities:
    #     print([w for w in activity.widgets()])

    berts_project=get_project(url="http://10.0.145.204:8000", username="admin", password="pass",
                              scope_id="13fb3e43-69d7-4096-98da-7f50347d4f6d")
    all_activities = berts_project.activities(activity_type=ActivityType.TASK)
    for activity in all_activities:
        act_widgets = list(activity.widgets())
        widgets_json = [w._json_data for w in act_widgets]
        with Path('act_{}_widgets.json'.format(activity.id[-6:])).open('w') as fd:
            json.dump(widgets_json, fd, indent=2, ensure_ascii=True)

        print([w for w in act_widgets])

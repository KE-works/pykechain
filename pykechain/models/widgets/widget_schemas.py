from copy import deepcopy

from pykechain.enums import WidgetTypes

widget_meta_schema = {
    "$schema": "https://json-schema.org/schema#",
    "title": "Toplevel Widget Meta schema",
    "type": "object",
    "additionalProperties": True,
    "properties": {},
    "definitions": {
        "uuidString": {"type": "string",
                       "pattern": "^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$"},
        "nullUuidString": {"type": ["string", "null"],
                           "pattern": "^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$"},
        "nullString": {"type": ["string", "null"]},
        "positiveInteger": {"type": ["integer", "null"], "minimum": 0},
        "booleanNull": {"type": ["boolean", "null"]}
    }
}

def_nullstring = {"$ref": "#/definitions/nullString"}
def_uuid = {"$ref": "#/definitions/uuidString"}
def_nulluuid = {"$ref": "#/definitions/nullUuidString"}
def_bool = {"$ref": "#/definitions/booleanNull"}
def_positive_int = {"$ref": "#/definitions/positiveInteger"}


def get_widget_meta_schema(widget_type=WidgetTypes.UNDEFINED):
    return widget_meta_schema


# attachmentviewer_meta_schema = widget_meta_schema.update({
#     "properties": {
#         "propertyInstanceId": {"$ref": "#/definitions/uuidString"},
#         "customHeight": {"$ref": "#/defintions/nullPositiveInteger"},
#         "activityId": {"$ref": "#/definitions/uuidString"},
#         "showTitleValue": {"type": ["string", "null"], "enum": ["Custom Value", "Default"]},
#         "customTitle": {"$ref": "#/definitions/nullString"},
#     }
# })

attachmentviewer_meta_schema = deepcopy(widget_meta_schema)
attachmentviewer_meta_schema.update({
    "title": "AttachmentViewer Widget Meta schema",
    "properties": {
        # kecard
        "showTitleValue": {"type": "string", "enum": ["No title", "Custom title", "Default"]},
        "customTitle": def_nullstring,
        "customHeight": def_positive_int,
        "showHeightValue": {"type": "string", "enum": ["Auto", "Automatic height"]},
        "collapsed": def_bool,
        "collapsible": def_bool,
        "noBackground": def_bool,
        "noPadding": def_bool,
        "isDisabled": def_bool,
        # attachment
        "propertyInstanceId": {"$ref": "#/definitions/uuidString"},
        "activityId": {"$ref": "#/definitions/uuidString"},
        "alignment": {"$ref": "#/definitions/booleanNull"}
    },
    "additionalProperties": False,
    "required": ["propertyInstanceId", "activityId"]
})

# see: KEC3FE - src/widgets/widgetConfigurationDialog/configurator/configurators/WidgetConfigurator.kecard.js:206
html_meta_schema = deepcopy(widget_meta_schema)
html_meta_schema.update({
    "title": "HTML Widget Meta schema",
    "properties": {
        # kecard
        "showTitleValue": {"type": "string", "enum": ["No title", "Custom title", "Default"]},
        "customTitle": def_nullstring,
        "customHeight": def_positive_int,
        "showHeightValue": {"type": "string", "enum": ["Auto", "Automatic height"]},
        "collapsed": def_bool,
        "collapsible": def_bool,
        "noBackground": def_bool,
        "noPadding": def_bool,
        "isDisabled": def_bool,
        # widget
        "activityId": def_uuid,
        "html": def_nullstring
    },
    "additionalProperties": False,
    "required": ["html"]
})

navbar_meta_schema = deepcopy(widget_meta_schema)
navbar_meta_schema.update({
    "title": "Navigation Bar Widget Meta schema",
    "properties": {
        "activityId": def_uuid,
        "isDisabled": def_bool,
        "alignment": {"type": "string", "enum": ["center", "left"]},
        "taskButtons": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                # "required": ["name"],
                "properties": {
                    "activityId": def_nulluuid,
                    "name": def_nullstring,
                    "emphasized": def_bool,
                    "emphasize": def_bool,  # TODO: one of these must go.
                    "customText": def_nullstring,
                    "isDisabled": def_bool,
                    "link": def_nullstring,
                }
            }
        }
    },
    "additionalProperties": False,
    "required": ["activityId", "alignment", "taskButtons"]
})

# "name": "propertyGridWidget",
#         "meta": {
#             "showHeaders": False,
#             "activityId": "4d5c31f0-d57a-4452-a6cc-41483c869e16",
#             "showColumns": [],
#             "collapsible": True,
#             "showTitleValue": "Custom title",
#             "customTitle": "Settings",
#             "partInstanceId": "7241ccfa-3a89-4114-b60a-202c9dac9f7e",
#             "collapsed": True,
#             "customHeight": None,
#             "showHeightValue": "Automatic height"
#         }
property_grid_meta_schema = deepcopy(widget_meta_schema)
property_grid_meta_schema.update({
    "title": "Propertygrid Widget Meta schema",
    "properties": {
        # kecard
        "showTitleValue": {"type": "string", "enum": ["No title", "Custom title", "Default"]},
        "customTitle": def_nullstring,
        "customHeight": def_positive_int,
        "showHeightValue": {"type": "string", "enum": ["Auto", "Automatic height"]},
        "collapsed": def_bool,
        "collapsible": def_bool,
        "noBackground": def_bool,
        "noPadding": def_bool,
        "isDisabled": def_bool,

        # columns
        "columns": {"type": "array", "items": [def_nulluuid]},

        # grid
        "activityId": def_uuid,
        "partModelId": def_uuid,
        "showHeaders": def_bool,
        "hideHeaders": def_bool,
        "showColumns": {
            "type": "array",
            "items": [def_nullstring]
        },
        "partInstanceId": def_uuid,
    },
    "additionalProperties": False,
    "required": ["activityId", "partInstanceId"]
})

# "name": "multiColumnWidget",
#         "meta": {
#             "height": 184,
#             "customTitle": "Trailer details",
#             "collapsed": False,
#             "collapsible": False,
#             "showTitleValue": "Custom title"
#         }

multicolumn_meta_schema = deepcopy(widget_meta_schema)
multicolumn_meta_schema.update({
    "title": "Multicolumn Widget Meta schema",
    "properties": {
        # kecard
        "showTitleValue": {"type": "string", "enum": ["No title", "Custom title", "Default"]},
        "customTitle": def_nullstring,
        "customHeight": def_positive_int,
        "showHeightValue": {"type": "string", "enum": ["Auto", "Automatic height"]},
        "collapsed": def_bool,
        "collapsible": def_bool,
        "noBackground": def_bool,
        "noPadding": def_bool,
        "isDisabled": def_bool,
        # multicolumn
        "activityId": def_uuid,
        "height": def_positive_int,
    },
    "additionalProperties": False,
    "required": []
})

# "name": "serviceWidget",
#         "meta": {
#             "showDownloadLog": False,
#             "serviceId": "2b755e56-08c0-4e5b-8b5b-08bd636fcf9e",
#             "showTitleValue": "No title",
#             "customTitle": None,
#             "emphasizeButton": True,
#             "customText": "Submit vehicle specification",
#             "showButtonValue": "Custom text"
#         }

service_meta_schema = deepcopy(widget_meta_schema)
service_meta_schema.update({
    "title": "Service Widget Meta schema",
    "properties": {
        # kecard
        "showTitleValue": {"type": "string", "enum": ["No title", "Custom title", "Default"]},
        "customTitle": def_nullstring,
        "customHeight": def_positive_int,
        "showHeightValue": {"type": "string", "enum": ["Auto", "Automatic height"]},
        "collapsed": def_bool,
        "collapsible": def_bool,
        "noBackground": def_bool,
        "noPadding": def_bool,
        "isDisabled": def_bool,
        # service
        "activityId": def_uuid,
        "showDownloadLog": def_bool,
        "showLog": def_bool,
        "serviceId": def_uuid,
        "emphasizeButton": {"type": ["string", "boolean", "null"]},
        ## needs to be boolean - but old bike_fixtures do have 'false' instead of False
        "customText": def_nullstring,
        "showButtonValue": {"type": "string", "enum": ["Custom text", "Default", "No text"]},
    },
    "additionalProperties": False,
    "required": ["serviceId"]
})

# "name" : metapanelwidget
# {"showAll": true}
# {'activityId': 'e448e38b-dcc3-4651-bde9-55fa2d1d1ad0',
#      'progressBarSettings': {'colorCompleted': 'rgba(51, 148, 71, 1)',
#                              'colorInProgress': 'rgba(51, 148, 71, 1)',
#                              'colorInProgressBackground': '#eee',
#                              'colorNoProgress': '#eee',
#                              'customHeight': 4,
#                              'showProgressText': False},
#      'showAll': False,
#      'showAssignees': True,
#      'showBreadCrumb': True,
#      'showDueDate': True,
#      'showMenu': True,
#      'showMenuDownloadPDF': True,
#      'showProgress': True,
#      'showProgressBar': True,
#      'showStartDate': True,
#      'showStatus': True,
#      'showTitle': True}


metapanel_meta_schema = deepcopy(widget_meta_schema)
metapanel_meta_schema.update({
    "title": "Metapanel Widget Meta schema",
    "properties": {
        "showAll": def_bool,
        "showTitle": def_bool,
        "showProgress": def_bool,
        "showAssignees": def_bool,
        "showDueDate": def_bool,
        "showStartDate": def_bool,
        "showStatus": def_bool,
        "showBreadCrumb": def_bool,
        "showMenu": def_bool,
        "showMenuDownloadPDF": def_bool,
        "activityId": def_uuid,

        # progress
        "progressBarSettings": {
            "type": "object",
            "properties": {
                "colorCompleted": def_nullstring,
                "colorInProgress": def_nullstring,
                "colorNoProgress": def_nullstring,
                "colorInProgressBackground": def_nullstring,
                "showProgressText": def_bool,
                "customHeight": def_positive_int,
            },
            "additionalProperties": False},
        "showProgressBar": def_bool,
    },
    "additionalProperties": False
})

# FILTEREDGRID
# {"activityId": "9898b39b-698e-4990-8c06-1b538b3bcaf3", "customTitle": "Task Table - Frame",
#  "partModelId": "70c502a0-fa20-461b-9f3b-1a73ebf74c43", "customHeight": null, "showTitleValue": "Custom title",
#  "showHeightValue": "Auto", "addButtonVisible": true, "parentInstanceId": "fbbb2854-830e-43a8-abad-6e46d9942e2c",
#  "editButtonVisible": true, "deleteButtonVisible": true, "downloadButtonVisible": true,
#  "incompleteRowsButtonVisible": true}

filteredgrid_meta_schema = deepcopy(widget_meta_schema)
filteredgrid_meta_schema.update({
    "title": "Filteredgrid Widget Meta schema",
    "properties": {
        # kecard
        "showTitleValue": {"type": "string", "enum": ["No title", "Custom title", "Default"]},
        "customTitle": def_nullstring,
        "customHeight": def_positive_int,
        "showHeightValue": {"type": "string", "enum": ["Auto", "Automatic height"]},
        "collapsed": def_bool,
        "collapsible": def_bool,
        "noBackground": def_bool,
        "noPadding": def_bool,
        "isDisabled": def_bool,
        # grid
        "activityId": def_uuid,
        "partModelId": def_uuid,
        "parentInstanceId": def_uuid,
        "showCollapseFiltersValue": {"type": "string", "enum": ["Expanded", "Collapsed"]},  # compatibility
        "collapseFilters": def_bool,
        "parentPartModelId": def_uuid,
        "parentpartModelId": def_uuid,  # TODO: to be deprecated in the next version.
        # columns
        "columns": {"type": "array", "items": [def_nulluuid]},
        "sortedColumn": def_nullstring,
        "sortDirection": {"type": "string", "enum": ["ASC", "DESC"]},
        "hideHeaders": def_bool,
        "customPageSize": def_positive_int,
        # buttons
        "addButtonVisible": def_bool,
        "editButtonVisible": def_bool,
        "deleteButtonVisible": def_bool,
        "cloneButtonVisible": def_bool,
        "downloadButtonVisible": def_bool,
        "incompleteRowsVisible": def_bool,
        "incompleteRowsButtonVisible": def_bool,
        "primaryAddUiValue": def_bool,
        "primaryEditUiValue": def_bool,
        "primaryCloneUiValue": def_bool,
        "primaryDeleteUiValue": def_bool,
    },
    "additionalProperties": False,
    "required": ["activityId", "partModelId"]
})

supergrid_meta_schema = deepcopy(filteredgrid_meta_schema)
supergrid_meta_schema.update({
    "title": "Supergrid Widget Meta schema",
})
supergrid_meta_schema['properties'].update({
})

# "widget_type": "PROGRESS",
# "meta": {
# "activityId": "e448e38b-dcc3-4651-bde9-55fa2d1d1ad0",
# "customHeight": 25,
# "colorCompleted": "rgba(51, 148, 71, 1)",
# "colorInProgress": "#ff5600",
# "colorNoProgress": "#eee",
# "showProgressText": true,
# "colorInProgressBackground": "#FC7C3D"
# },

progress_meta_schema = deepcopy(widget_meta_schema)
progress_meta_schema.update({
    "title": "Progress Widget Meta schema",
    "additionalProperties": False,
    "required": ["activityId"],
    "properties": {
        # kecard
        "showTitleValue": {"type": "string", "enum": ["No title", "Custom title", "Default"]},
        "customTitle": def_nullstring,
        "customHeight": def_positive_int,
        "showHeightValue": {"type": "string", "enum": ["Auto", "Automatic height"]},
        "collapsed": def_bool,
        "collapsible": def_bool,
        "noBackground": def_bool,
        "noPadding": def_bool,
        "isDisabled": def_bool,
        # progress
        "activityId": def_uuid,
        "colorCompleted": def_nullstring,
        "colorInProgress": def_nullstring,
        "colorNoProgress": def_nullstring,
        "colorInProgressBackground": def_nullstring,
        "showProgressText": def_bool,
    }
})

# "widget_type": "SCOPE",
# "meta": {
# "tags": [],
# "teamId": "8c18c808-1816-4697-bdef-ebb990f75af7",
# "ordering": null,
# "collapsed": false,
# "noPadding": false,
# "activityId": "e448e38b-dcc3-4651-bde9-55fa2d1d1ad0",
# "collapsible": false,
# "customTitle": null,
# "customHeight": null,
# "noBackground": false,
# "showTitleValue": "Default"
# },

scope_meta_schema = deepcopy(widget_meta_schema)
scope_meta_schema.update({
    "title": "Scope Widget Meta schema",
    "additionalProperties": False,
    "required": ["activityId"],
    "properties": {
        # kecard
        "showTitleValue": {"type": "string", "enum": ["No title", "Custom title", "Default"]},
        "customTitle": def_nullstring,
        "customHeight": def_positive_int,
        "showHeightValue": {"type": "string", "enum": ["Auto", "Automatic height"]},
        "collapsed": def_bool,
        "collapsible": def_bool,
        "noBackground": def_bool,
        "noPadding": def_bool,
        "isDisabled": def_bool,
        # progress
        "activityId": def_uuid,
        "teamId": def_nulluuid,
        "ordering": def_nullstring,
        "tags": {"type": "array", "items": [def_nullstring]}

    }
})

# "widget_type": "NOTEBOOK",
# "meta": {
# "collapsed": false,
# "noPadding": false,
# "serviceId": "24b92f9e-5ac0-4095-85ae-217436b24d97",
# "activityId": "e448e38b-dcc3-4651-bde9-55fa2d1d1ad0",
# "collapsible": false,
# "customTitle": null,
# "customHeight": 800,
# "noBackground": false,
# "showTitleValue": "Default"
# },

notebook_meta_schema = deepcopy(widget_meta_schema)
notebook_meta_schema.update({
    "title": "Notebook Widget Meta schema",
    "additionalProperties": False,
    # "required": [""],
    "properties": {
        # kecard
        "showTitleValue": {"type": "string", "enum": ["No title", "Custom title", "Default"]},
        "customTitle": def_nullstring,
        "customHeight": def_positive_int,
        "showHeightValue": {"type": "string", "enum": ["Auto", "Automatic height"]},
        "collapsed": def_bool,
        "collapsible": def_bool,
        "noBackground": def_bool,
        "noPadding": def_bool,
        "isDisabled": def_bool,
        # progress
        "activityId": def_uuid,
        "serviceId": def_uuid,
    }
})

thirdpart_meta_schema = deepcopy(widget_meta_schema)
thirdpart_meta_schema.update({
    "title": "Scope Widget Meta schema",
    "additionalProperties": True,
    "required": ["subType"],
    "properties": {
        # kecard
        "showTitleValue": {"type": "string", "enum": ["No title", "Custom title", "Default"]},
        "customTitle": def_nullstring,
        "customHeight": def_positive_int,
        "showHeightValue": {"type": "string", "enum": ["Auto", "Automatic height"]},
        "collapsed": def_bool,
        "collapsible": def_bool,
        "noBackground": def_bool,
        "noPadding": def_bool,
        "isDisabled": def_bool,
        # thirdparty
        "subType": def_nullstring,  # this determines the specific widget to display
    }
})

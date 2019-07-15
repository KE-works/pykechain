from copy import deepcopy

widget_meta_schema = {
    "$schema": "http://json-schema.org/draft-06/schema#",
    "title": "Toplevel Widget Meta schema",
    "type": "object",
    "additionalProperties": False,
    "properties": {},
    "definitions": {
        "uuidString": {"type": "string",
                       "pattern": "^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$"},
        "nullUuidString": {"type": ["string", "null"],
                           "pattern": "^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$"},
        "nullString": {"type": ["string", "null"]},
        "positiveInteger": {"type": ["integer", "null", "string"], "minimum": 0},
        "booleanNull": {"type": ["boolean", "null"]}
    }
}

def_nullstring = {"$ref": "#/definitions/nullString"}
def_uuid = {"$ref": "#/definitions/uuidString"}
def_nulluuid = {"$ref": "#/definitions/nullUuidString"}
def_bool = {"$ref": "#/definitions/booleanNull"}
def_positive_int = {"$ref": "#/definitions/positiveInteger"}

#
# Attachmentviewer
#
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
        "alignment": {"type": ["array", "null"], "items": {"type": "string", "enum": ["left", "center", "right"]}}
    },
    "required": ["propertyInstanceId", "activityId"]
})

#
# Html
#
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
        "htmlContent": def_nullstring,  # this is migrated from 'html'.
        "html": def_nullstring
    },
    # "required": ["htmlContent"]
})

#
# Json
#
json_meta_schema = deepcopy(widget_meta_schema)
json_meta_schema.update({
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
        "jsonContent": def_nullstring  # this is migrated from 'html'.
    },
    # "required": ["jsonContent"]
})

#
# Navigationbar
#
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
    "required": ["activityId", "alignment", "taskButtons"]
})

#
# Propertygrid
#
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
    "required": ["activityId", "partInstanceId"]
})

#
# multicolumn
#

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
    "required": []
})

#
# Service
#
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
        # needs to be boolean - but old bike_fixtures do have 'false' instead of False
        "customText": def_nullstring,
        "showButtonValue": {"type": "string", "enum": ["Custom text", "Default", "No text"]},
    },
    "required": ["serviceId"]
})

#
# Metapanel
#
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
    }
})

#
# Filteredgrid
#
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
    "required": ["activityId", "partModelId"]
})

#
# Supergrid
#
supergrid_meta_schema = deepcopy(filteredgrid_meta_schema)
supergrid_meta_schema.update({
    "title": "Supergrid Widget Meta schema",
})

#
# Progress
#
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

#
# Scope
#
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
        # columns
        "showHeaders": def_bool,
        "hideHeaders": def_bool,
        "showColumns": {
            "type": "array",
            "items": [def_nullstring]
        },
        "sortedColumn": def_nullstring,
        "sortDirection": {"type": "string", "enum": ["ASC", "DESC"]},
        # scope
        "activityId": def_uuid,
        "teamId": def_nulluuid,
        "ordering": def_nullstring,
        "tags": {"type": "array", "items": [def_nullstring]}
    }
})

#
# Notebook
#
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

#
# Thirdparty
#
thirdpart_meta_schema = deepcopy(widget_meta_schema)
thirdpart_meta_schema.update({
    "title": "Scope Widget Meta schema",
    "additionalProperties": True,  # !important to allow all the properties you can come up with.
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

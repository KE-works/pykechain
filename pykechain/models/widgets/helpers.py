from typing import Dict, Optional, Union, Text

from six import text_type

from pykechain.exceptions import IllegalArgumentError
from pykechain.utils import is_uuid


def _retrieve_part_model(part_model, client):
    # type: (Union[Part2,Text], Client) -> Part2  # noqa
    """

    :param part:
    :return:
    """
    # Check whether the part_model is uuid type or class `Part`
    from pykechain.models import Part, Part2
    if isinstance(part_model, (Part, Part2)):
        return part_model
    elif isinstance(part_model, text_type) and is_uuid(part_model):
        part_model_id = part_model
        part_model = client.model(id=part_model_id)
        return part_model
    else:
        raise IllegalArgumentError("When using the add_super_grid_widget, part_model must be a Part or Part id. "
                                   "Type is: {}".format(type(part_model)))


def _retrieve_parent_instance(parent_instance, client):
    # type: (Optional[Union[Part2, Text]], Client) -> Part2  # noqa
    # Check whether the parent_part_instance is uuid type or class `Part`
    from pykechain.models import Part, Part2
    if isinstance(parent_instance, (Part, Part2)):
        return parent_instance
    elif isinstance(parent_instance, text_type) and is_uuid(parent_instance):
        parent_instance_id = parent_instance
        parent_instance = client.part(id=parent_instance_id)
        return parent_instance
    elif isinstance(parent_instance, type(None)):
        return parent_instance
    else:
        raise IllegalArgumentError("When using the add_super_grid_widget, parent_part_instance must be a "
                                   "Part, Part id or None. Type is: {}".format(type(parent_instance)))


def _retrieve_sort_property_id(sort_property):
    # type: (Optional[Union[Property2,Text]]) -> Optional[Text]  # noqa

    # Check whether the sort_property is uuid type or class `Property`
    from pykechain.models import Property2
    if isinstance(sort_property, Property2):
        return sort_property.id
    elif isinstance(sort_property, text_type) and is_uuid(sort_property):
        return sort_property
    elif isinstance(sort_property, type(None)):
        return None
    else:
        raise IllegalArgumentError("When using the add_paginated_grid_widget, sort_property must be a "
                                   "Property, Property id or None. Type is: {}".format(type(sort_property)))


def _set_title(meta, custom_title, default_title=None):
    # type: (Dict, Optional[Union[Text, bool]], Optional[Text]) -> (Dict, Text)
    if custom_title is False:
        show_title_value = "Default"
        title = default_title
    elif custom_title is None:
        show_title_value = "No title"
        title = ''
    else:
        show_title_value = "Custom title"
        title = custom_title

    meta.update({
        "showTitleValue": show_title_value,
        "customTitle": title
    })

    return meta, title


def _initiate_meta(kwargs, activity_id):
    custom_height = kwargs.get("customHeight", None)
    if custom_height:
        show_height_value = "Custom Height"
    else:
        show_height_value = "Auto"

    kecard = {
        "activityId": str(activity_id),
        "collapsed": kwargs.get("collapsed", False),
        "collapsible": kwargs.get("collapsible", False),
        "noBackground": kwargs.get("noBackground", False),
        "noPadding": kwargs.get("noPadding", False),
        "isDisabled": kwargs.get("isDisabled", False),
        "customHeight": custom_height,
        "showHeightValue": show_height_value
    }
    return kecard

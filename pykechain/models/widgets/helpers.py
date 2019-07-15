from typing import Dict, Optional, Union, Text

from six import text_type

from pykechain.exceptions import IllegalArgumentError
from pykechain.utils import is_uuid


def _retrieve_object(ke_chain_object, client):
    # type: (Union[Part2, Property2, Text], Client) -> (Union[Part2, Property2])  # noqa
    """

    :param part:
    :return:
    """
    # Check whether the part_model is uuid type or class `Part`
    from pykechain.models import Part, Part2, Property, Property2
    if isinstance(ke_chain_object, (Part, Part2, Property, Property2)):
        return ke_chain_object
    elif isinstance(ke_chain_object, text_type) and is_uuid(ke_chain_object):
        part_model_id = ke_chain_object
        part_model = client.model(id=part_model_id)
        return part_model
    else:
        raise IllegalArgumentError("When adding the widget, ke_chain_object must be a Part, Property,"
                                   " Part id or Property id. Type is: {}".format(type(ke_chain_object)))


def _retrieve_object_id(ke_chain_object):
    # type: (Optional[Union[Part2, Property2, Text]]) -> Optional[Text]  # noqa
    # Check whether the parent_part_instance is uuid type or class `Part`
    from pykechain.models import Part, Part2, Property, Property2
    if isinstance(ke_chain_object, (Part, Part2, Property, Property2)):
        return ke_chain_object.id
    elif isinstance(ke_chain_object, text_type) and is_uuid(ke_chain_object):
        return ke_chain_object
    elif isinstance(ke_chain_object, type(None)):
        return None
    else:
        raise IllegalArgumentError("When adding the widget, ke_chain_object must be a Part, Property,"
                                   " Part id or Property id. Type is: {}".format(type(ke_chain_object)))


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

    if not title:
        title = default_title

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

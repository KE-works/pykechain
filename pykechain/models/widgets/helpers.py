from typing import Dict, Optional, Union, Text

from six import text_type

from pykechain.exceptions import IllegalArgumentError
from pykechain.utils import is_uuid, snakecase, camelcase


def _retrieve_object(ke_chain_object, client):
    # type: (Union[Part2, Property2, Team, Text], Client) -> (Union[Part2, Team, Property2])  # noqa
    """

    :param part:
    :return:
    """
    # Check whether the part_model is uuid type or class `Part`
    from pykechain.models import Part, Part2, Property, Property2, Team
    if isinstance(ke_chain_object, (Part, Part2, Property, Property2, Team)):
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


def _initiate_meta(kwargs, activity, ignores=()):
    """Initate the widget meta definition.

    Mainly ensure to initiate the correct keys that are common to (most) widgets like the keys related
    to the so called kecard (the card object around the widget in the frontend. These keys are: `collapsed`,
    `collapsible`, `noBackground`, `noPadding`, `isDisabled`, `customHeight`, `showHeightValue`. Also the
    the `custom_height` is initiated.

    If you want to be sure that some keys are never present in the returned meta (eg 'customHeight')
    than you may want to add them to ignores.

    :param kwargs: the keyword arguments provided to the widget function which are checked for the kecard definition
    :type kwargs: dict
    :param activity: uuid or `activity2` object
    :type activity: Activity2 or basestring
    :param ignores: list or tuple of keys to ensure they are not present in the initated meta on return
    :type ignores: list or tuple
    :return: kecard dictionary
    :rtype: dict
    """
    meta = dict(activityId=str(_retrieve_object_id(activity)))
    keys_in_kwargs = ["collapsed", "collapsible", "noBackground", "noPadding", "isDisabled"]
    # also add the keys' in their snake case appearance so noPadding and no_padding, customHeight and custom_height
    keys_in_kwargs += [snakecase(k) for k in keys_in_kwargs]

    # initiate the meta based on known kwarg arguments
    for key in list(set(keys_in_kwargs)):
        if key in kwargs:
            meta[camelcase(key)] = kwargs.pop(key)

    # we check for custom_height specifcally and deal with it.
    if snakecase('customHeight') in kwargs:
        custom_height = kwargs.pop(snakecase("customHeight"))
        if custom_height is not None:
            meta['customHeight'] = custom_height
        else:
            meta['showHeightValue'] = "Auto"

    # remove the 'ignores' from the meta
    for key in ignores:
        if key in meta:
            del meta[key]

    return meta

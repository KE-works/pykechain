from typing import Dict, Optional, Union, Text, Tuple, List, Callable

from pykechain.enums import Category, PropertyType, WidgetTitleValue
from pykechain.exceptions import IllegalArgumentError
from pykechain.models.input_checks import check_enum
from pykechain.utils import is_uuid, snakecase, camelcase

# these are the common keys to all kecards.
KECARD_COMMON_KEYS = ["collapsed", "collapsible", "noBackground", "noPadding", "isDisabled", "isMerged"]


def _retrieve_object(obj: Union['Base', Text], method: Callable) -> Union['Base']:
    """
    Object if object or uuid of object is provided as argument.

    :param obj: object or uuid to retrieve the object for
    :type obj: :class:`Base` or basestring
    :param method: client object to retrieve the object if only uuid is provided.
    :type method: `Client`
    :return: object based on the object or uuid of the objet
    :rtype: `Part2` or `Team` or `Property2`
    :raises APIError: If the object could not be retrieved based on the UUID
    :raises IllegalArgumentError: if the object provided is not a Part, Property2 or UUID.
    """
    # Check whether the part_model is uuid type or class `Part`
    from pykechain.models import Part2, Property2, Service, Team
    if isinstance(obj, (Part2, Property2, Service, Team)):
        return obj
    elif isinstance(obj, str) and is_uuid(obj):
        obj_id = obj
        obj = method(id=obj_id)
        return obj
    else:
        raise IllegalArgumentError("When adding the widget, obj must be a Part, Property, Service, Team, "
                                   " Part id, Property id, Service id or Team id. Type is: {}".format(type(obj)))


def _retrieve_object_id(obj: Optional[Union['Base', Text]]) -> Optional[Text]:
    """
    Object id if object or uuid of object is provided as argument.

    :param obj: object or uuid to retrieve the object id for
    :type obj: :class:`Base` or basestring
    :return: object based on the object or uuid of the object
    :rtype: basestring or None
    :raises APIError: If the object could not be retrieved based on the UUID
    :raises IllegalArgumentError: if the object provided is not a Base instance or UUID.
    """
    # Check whether the obj is an object of any subclass of Base, or uuid type
    from pykechain.models import Base
    if issubclass(type(obj), Base):
        return obj.id
    elif isinstance(obj, str) and is_uuid(obj):
        return obj
    elif isinstance(obj, type(None)):
        return None
    else:
        raise IllegalArgumentError("When adding the widget, obj must be an instance of `Base` or an object id. "
                                   "Type is: {}".format(type(obj)))


def _set_title(meta: Dict,
               title: Optional[Union[Text, bool]] = None,
               default_title: Optional[Text] = None,
               show_title_value: Optional[WidgetTitleValue] = None,
               **kwargs) -> Tuple[Dict, Text]:
    """
    Set the customTitle in the meta based on provided optional custom title or default.

    This will inject into the meta the `customTitle` and `showTitleValue` if the `title` is provided as
    argument, otherwise it will inject the `defaultTitle`. It returns the meta definition of the widget and the
    title of the widget (to be used to set `widget.title`).

    :param meta: meta dictionary to augment
    :type meta: dict
    :param title: A title for the multi column widget
            * False: use the default title
            * String value: use the title
            * None: No title at all.
    :type title: basestring or bool or None
    :param default_title: (optional) If title is False, the default title is injected as title
    :type default_title: basestring or None
    :param show_title_value: (optional) Specify how the title is displayed, regardless of other inputs.
    :type show_title_value: WidgetTitleValue
    :return: tuple of meta and the title
    :rtype: Tuple[Dict,Text]
    :raises IllegalArgumentError: When illegal (combination) of arguments are set.
    """
    check_enum(show_title_value, WidgetTitleValue, 'show_title_value')

    if show_title_value is None:
        if title is False:
            show_title_value = WidgetTitleValue.DEFAULT
        elif title is None or title == '':
            show_title_value = WidgetTitleValue.NO_TITLE
        else:
            show_title_value = WidgetTitleValue.CUSTOM_TITLE

    if show_title_value == WidgetTitleValue.DEFAULT:
        title_meta = None
        if default_title is None:
            raise IllegalArgumentError("If `title` is set to False the `default_title` is used and cannot be None. "
                                       "Provide a `default_title` argument and ensure it is not None.")
        title_ref = default_title
    else:
        title_meta = title
        title_ref = title

    meta.update({
        "showTitleValue": show_title_value,
        "customTitle": title_meta,
    })
    return meta, title_ref


def _initiate_meta(kwargs, activity, ignores=()):
    """
    Init Widget meta definition.

    Mainly ensure to initiate the correct keys that are common to (most) widgets like the keys related
    to the so called kecard (the card object around the widget in the frontend. These keys are: `collapsed`,
    `collapsible`, `noBackground`, `noPadding`, `isDisabled`, `customHeight`. Also the
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
    # also add the keys' in their snake case appearance so noPadding and no_padding, customHeight and custom_height
    keys_in_kwargs = KECARD_COMMON_KEYS + [snakecase(k) for k in KECARD_COMMON_KEYS]

    # initiate the meta based on known kwarg arguments
    for key in list(set(keys_in_kwargs)):
        if key in kwargs:
            meta[camelcase(key)] = kwargs.pop(key)

    # we check for custom_height specifically and deal with it.
    if snakecase('customHeight') in kwargs:
        meta['customHeight'] = kwargs.pop(snakecase("customHeight"))

    # remove the 'ignores' from the meta
    for key in ignores:
        if key in meta:
            del meta[key]

    return meta


def _check_prefilters(part_model: 'Part2', prefilters: Dict) -> List[Text]:  # noqa: F821
    """
    Check the pre-filters on a `FilteredGridWidget` or `MultiReferenceProperty2.

    The prefilters should comply to the prefilters schema as present in the backend.

    ```
    "prefilters": {
        "type": ["object", "null"],
        "additionalProperties": True,
        "properties": {
            "property_value": def_nullstring,
            "name__icontains": def_nullstring
        }
    }
    ```

    :param part_model: The part model of which the properties are filtered.
    :param prefilters: Dictionary with prefilters.
    :raises IllegalArgumentError: when the type of the input is provided incorrect.
    """
    from pykechain.models import Property2

    property_models = prefilters.get('property_models', [])  # type: List[Property2, Text]  # noqa
    values = prefilters.get('values', [])
    filters_type = prefilters.get('filters_type', [])

    if any(len(lst) != len(property_models) for lst in [values, filters_type]):
        raise IllegalArgumentError('The lists of "property_models", "values" and "filters_type" should be the '
                                   'same length.')

    list_of_prefilters = []
    for prop, value, filter_type in zip(property_models, values, filters_type):
        if is_uuid(prop):
            prop = part_model.property(prop)  # the finder can handle uuid, name or ref

        if not isinstance(prop, Property2) or prop.category != Category.MODEL:
            raise IllegalArgumentError(
                'Pre-filters can only be set on Property models, received "{}".'.format(prop))

        elif part_model.id != prop.part_id:
            raise IllegalArgumentError(
                'Pre-filters can only be set on properties belonging to the selected Part model, found '
                'selected Part model "{}" and Properties belonging to "{}"'.format(part_model.name,
                                                                                   prop.part.name))
        else:
            if prop.type == PropertyType.BOOLEAN_VALUE:
                value = str(value).lower()
            new_pre_filter = ':'.join([prop.id, str(value), filter_type])
            list_of_prefilters.append(new_pre_filter)
    return list_of_prefilters


def _check_excluded_propmodels(part_model: 'Part2', property_models: List['AnyProperty']) -> List['AnyProperty']:
    """
    Validate the excluded property models of the referenced part.

    :param part_model: Part model that is referenced
    :param property_models: Properties of the part model to be excluded.
    :return: list of property IDs
    :rtype list
    :raises IllegalArgumentError: whenever the properties are not of category MODEL or do not belong to the part model.
    """
    from pykechain.models import Property2
    from pykechain.models import Part2

    if not isinstance(part_model, Part2):
        raise IllegalArgumentError('`part_model` must be a Part2 object, "{}" is not.'.format(part_model))

    list_of_propmodels_excl = list()  # type: List['AnyProperty']
    for property_model in property_models:
        if is_uuid(property_model):
            property_model = part_model.property(property_model)
        elif not isinstance(property_model, Property2):
            raise IllegalArgumentError('A part reference property can only exclude `Property` models or their UUIDs, '
                                       'found type "{}"'.format(type(property_model)))

        if property_model.category != Category.MODEL:
            raise IllegalArgumentError('A part reference property can only exclude `Property` models, found '
                                       'category "{}" on property "{}"'.format(property_model.category,
                                                                               property_model.name))
        elif part_model.id != property_model.part_id:
            raise IllegalArgumentError(
                'A part reference property can only exclude properties belonging to the referenced Part model, '
                'found referenced Part model "{}" and Properties belonging to "{}"'.format(
                    part_model.name, property_model.part.name))
        else:
            list_of_propmodels_excl.append(property_model.id)
    return list_of_propmodels_excl

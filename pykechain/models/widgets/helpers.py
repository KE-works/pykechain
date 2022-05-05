import warnings
from typing import Dict, Optional, Union, Tuple, List, Callable

from pykechain.enums import (
    Category,
    PropertyType,
    WidgetTitleValue,
    ActivityType,
    CardWidgetLinkValue,
    KEChainPages,
    CardWidgetKEChainPageLink,
    LinkTargets,
    ImageFitValue,
    CardWidgetImageValue,
)
from pykechain.exceptions import IllegalArgumentError
from pykechain.models.input_checks import check_enum, check_base
from pykechain.models.value_filter import PropertyValueFilter
from pykechain.models.widgets.enums import MetaWidget, AssociatedObjectId
from pykechain.utils import is_uuid, snakecase, camelcase

# these are the common keys to all kecards.
KECARD_COMMON_KEYS = [
    MetaWidget.COLLAPSED,
    MetaWidget.COLLAPSIBLE,
    MetaWidget.NO_BACKGROUND,
    MetaWidget.NO_PADDING,
    MetaWidget.IS_DISABLED,
    MetaWidget.IS_MERGED,
]

TITLE_TYPING = Optional[Union[type(None), str, bool]]


def _retrieve_object(obj: Union["Base", str], method: Callable) -> Union["Base"]:
    """
    Object if object or uuid of object is provided as argument.

    :param obj: object or uuid to retrieve the object for
    :type obj: :class:`Base` or basestring
    :param method: client object to retrieve the object if only uuid is provided.
    :type method: `Client`
    :return: object based on the object or uuid of the objet
    :rtype: `Part` or `Team` or `Property`
    :raises APIError: If the object could not be retrieved based on the UUID
    :raises IllegalArgumentError: if the object provided is not a Part, Property or UUID.
    """
    # Check whether the part_model is uuid type or class `Part`
    from pykechain.models import Part, Property, Service, Team

    if isinstance(obj, (Part, Property, Service, Team)):
        return obj
    elif isinstance(obj, str) and is_uuid(obj):
        obj_id = obj
        obj = method(id=obj_id)
        return obj
    else:
        raise IllegalArgumentError(
            "When adding the widget, obj must be a Part, Property, Service, Team, "
            " Part id, Property id, Service id or Team id. Type is: {}".format(
                type(obj)
            )
        )


def _retrieve_object_id(obj: Optional[Union["Base", str]]) -> Optional[str]:
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
        raise IllegalArgumentError(
            "When adding the widget, obj must be an instance of `Base` or an object id. "
            "Type is: {}".format(type(obj))
        )


def _set_title(
    meta: Dict,
    title: TITLE_TYPING = None,
    show_title_value: Optional[WidgetTitleValue] = None,
    **kwargs,
) -> Tuple[Dict, str]:
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
    :param show_title_value: (optional) Specify how the title is displayed, regardless of other inputs.
    :type show_title_value: WidgetTitleValue
    :return: tuple of meta and the title
    :rtype: Tuple[Dict,Text]
    :raises IllegalArgumentError: When illegal (combination) of arguments are set.
    """
    check_enum(show_title_value, WidgetTitleValue, "show_title_value")

    if show_title_value is None:
        if title is False:
            show_title_value = WidgetTitleValue.DEFAULT
            title = None
        elif title is None or title == "":
            show_title_value = WidgetTitleValue.NO_TITLE
            title = None
        else:
            show_title_value = WidgetTitleValue.CUSTOM_TITLE

    if show_title_value == WidgetTitleValue.DEFAULT or title is False:
        title = None

    meta.update(
        {
            MetaWidget.SHOW_TITLE_VALUE: show_title_value,
            MetaWidget.CUSTOM_TITLE: title,
        }
    )
    return meta, title


def _set_description(
    meta: Dict, description: Optional[Union[str, bool]] = None, **kwargs
) -> Dict:
    """
    Set the customDescription in the meta based on provided optional custom description or no description.

    This will inject into the meta the `customDescription` and `showDescriptionValue` if the `description` is provided
    as argument, otherwise it will inject 'no description'. It returns the meta definition of the widget.

    :param meta: meta dictionary to augment
    :type meta: dict
    :param description: A description for the widget
            * String value: use the description
            * None or False: No description at all.
    :type description: basestring or None or bool

    :return: meta dictionary
    :rtype: dict
    :raises IllegalArgumentError: When description is neither str, bool or None.
    """
    if description is False or description is None:
        show_description_value = MetaWidget.DESCRIPTION_OPTION_NOTHING
        description = ""
    elif isinstance(description, str):
        show_description_value = MetaWidget.DESCRIPTION_OPTION_CUSTOM
    else:
        raise IllegalArgumentError(
            "When using the add_card_widget or add_service_card_widget, 'description' must be "
            "'text_type' or None or False. Type is: {}".format(type(description))
        )
    meta.update(
        {
            MetaWidget.SHOW_DESCRIPTION_VALUE: show_description_value,
            MetaWidget.CUSTOM_DESCRIPTION: description,
        }
    )
    return meta


def _set_link(
    meta: Dict,
    link: Optional[Union[type(None), str, bool, KEChainPages]] = None,
    link_value: Optional[CardWidgetLinkValue] = None,
    link_target: Optional[Union[str, LinkTargets]] = LinkTargets.SAME_TAB,
    **kwargs,
) -> Dict:
    """
    Set the link in the meta based on provided optional custom link.

    This will inject into the meta the `customLink` and `showLinkValue` if the `link` is provided
    as argument, otherwise it will inject 'no link'. It returns the meta definition of the widget.

    :param meta: meta dictionary to augment
    :type meta: dict
    :param link: Where the card widget refers to. This can be one of the following:
        * None (default): no link
        * task: another KE-chain task, provided as an Activity object or its UUID
        * String value: URL to a webpage
        * KE-chain page: built-in KE-chain page of the current scope
    :type link: basestring or None or bool or KEChainPages
    :param link_value: Overwrite the default link value (obtained from the type of the link)
    :type link_value: CardWidgetLinkValue
    :param link_target: how the link is opened, one of the values of CardWidgetLinkTarget enum.
    :type link_target: CardWidgetLinkTarget

    :return: meta dictionary
    :rtype: dict
    :raises IllegalArgumentError: When illegal (combination) of arguments are set.
    """
    meta["linkTarget"] = check_enum(link_target, LinkTargets, "link_target")

    from pykechain.models import Activity

    if isinstance(link, Activity):
        if link.activity_type == ActivityType.TASK:
            default_link_value = CardWidgetLinkValue.TASK_LINK
        else:
            default_link_value = CardWidgetLinkValue.TREE_VIEW

        meta.update(
            {
                MetaWidget.CUSTOM_LINK: link.id,
                MetaWidget.SHOW_LINK_VALUE: default_link_value,
            }
        )
    elif isinstance(link, str) and is_uuid(link):
        meta.update(
            {
                MetaWidget.CUSTOM_LINK: link,
                MetaWidget.SHOW_LINK_VALUE: CardWidgetLinkValue.TASK_LINK,
            }
        )
    elif link is None or link is False:
        meta.update(
            {
                MetaWidget.CUSTOM_LINK: None,
                MetaWidget.SHOW_LINK_VALUE: CardWidgetLinkValue.NO_LINK,
            }
        )
    elif link in KEChainPages.values():
        meta.update(
            {
                MetaWidget.CUSTOM_LINK: "",
                MetaWidget.SHOW_LINK_VALUE: CardWidgetKEChainPageLink[link],
            }
        )
    else:
        meta.update(
            {
                MetaWidget.CUSTOM_LINK: link,
                MetaWidget.SHOW_LINK_VALUE: CardWidgetLinkValue.EXTERNAL_LINK,
            }
        )

    if link_value is not None:
        meta.update(
            {
                MetaWidget.SHOW_LINK_VALUE: check_enum(
                    link_value, CardWidgetLinkValue, "link_value"
                ),
            }
        )

    return meta


def _set_image(
    meta: Dict,
    image: Optional["AttachmentProperty"] = None,
    image_fit: Optional[Union[str, ImageFitValue]] = ImageFitValue.CONTAIN,
    **kwargs,
) -> Dict:
    """
    Set the image in the meta based on provided optional custom link.

    This will inject into the meta the `customImage` and `showImageValue` if the `image` is provided
    as argument, otherwise it will inject 'no link'. It returns the meta definition of the widget.

    :param meta: meta dictionary to augment
    :type meta: dict
    :param image: AttachmentProperty providing the source of the image shown in the card widget.
    :type image: AttachmentProperty or None
    :param image_fit: how the image on the card widget is displayed
    :type image_fit: ImageFitValue

    :return: meta dictionary
    :rtype: dict
    :raises IllegalArgumentError: When illegal `image` type is used.
    """
    meta[MetaWidget.IMAGE_FIT] = check_enum(image_fit, ImageFitValue, "image_fit")

    from pykechain.models import Property

    if isinstance(image, Property) and image.type == PropertyType.ATTACHMENT_VALUE:
        meta.update(
            {
                MetaWidget.CUSTOM_IMAGE: f"/api/v3/properties/{image.id}/preview",
                MetaWidget.SHOW_IMAGE_VALUE: CardWidgetImageValue.CUSTOM_IMAGE,
            }
        )
    elif image is None:
        meta.update(
            {
                MetaWidget.CUSTOM_IMAGE: None,
                MetaWidget.SHOW_IMAGE_VALUE: CardWidgetImageValue.NO_IMAGE,
            }
        )
    else:
        raise IllegalArgumentError(
            "When using the add_card_widget or add_service_card_widget, 'image' must be an "
            "'AttachmentProperty' or None. Type is: {}".format(type(image))
        )
    return meta


def _set_button_text(
    meta: Dict, service: "Service", custom_button_text: TITLE_TYPING = False, **kwargs
) -> Dict:
    """
    Set the button text in the meta based on provided optional custom_button_text.

    This will inject into the meta the `customText` and `showButtonValue` if the `custom_button_text` is provided
    as argument, otherwise it will inject the Service name if False and no text if None. It returns the meta definition
    of the widget.

    :param meta: meta dictionary to augment
    :type meta: dict
    :param service: The Service to which the button will be coupled and will be ran when the button is pressed.
    :type service: :class:`Service` or UUID
    :param custom_button_text: A custom text for the button linked to the script
        * False (default): Script name
        * String value: Custom title
        * None: No title
    :type custom_button_text: bool or basestring or None

    :return: meta dictionary
    :rtype: dict
    :raises IllegalArgumentError: When illegal (combination) of arguments are set.
    """
    if custom_button_text is False:
        show_button_value = MetaWidget.BUTTON_TEXT_DEFAULT
        button_text = service.name
    elif custom_button_text is None:
        show_button_value = MetaWidget.BUTTON_NO_TEXT
        button_text = ""
    else:
        show_button_value = MetaWidget.BUTTON_TEXT_CUSTOM
        button_text = str(custom_button_text)
    meta.update(
        {
            MetaWidget.SHOW_BUTTON_VALUE: show_button_value,
            MetaWidget.CUSTOM_TEXT: button_text,
        }
    )
    return meta


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
    :param activity: uuid or `activity` object
    :type activity: Activity or basestring
    :param ignores: list or tuple of keys to ensure they are not present in the initated meta on return
    :type ignores: list or tuple
    :return: kecard dictionary
    :rtype: dict
    """
    meta = {AssociatedObjectId.ACTIVITY_ID: str(_retrieve_object_id(activity))}
    # also add the keys' in their snake case appearance so noPadding and no_padding, customHeight and custom_height
    keys_in_kwargs = KECARD_COMMON_KEYS + [snakecase(k) for k in KECARD_COMMON_KEYS]

    # initiate the meta based on known kwarg arguments
    for key in list(set(keys_in_kwargs)):
        if key in kwargs:
            meta[camelcase(key)] = kwargs.pop(key)

    # we check for custom_height specifically and deal with it.
    if snakecase(MetaWidget.CUSTOM_HEIGHT) in kwargs:
        meta[MetaWidget.CUSTOM_HEIGHT] = kwargs.pop(snakecase(MetaWidget.CUSTOM_HEIGHT))

    # remove the 'ignores' from the meta
    for key in ignores:
        if key in meta:
            del meta[key]

    return meta


def _check_prefilters(
    part_model: "Part", prefilters: Union[Dict, List]
) -> List[PropertyValueFilter]:  # noqa: F821
    """
    Check the format of the pre-filters.

    :param part_model: The part model of which the properties are filtered.
    :param prefilters: Dictionary or list with PropertyValueFilter objects.
    :returns: list of PropertyValueFilter objects
    :rtype list
    :raises IllegalArgumentError: when the type of the input is provided incorrect.
    """
    if isinstance(prefilters, dict):
        property_models: List[Property, str] = prefilters.get(
            MetaWidget.PROPERTY_MODELS, []
        )  # noqa
        values = prefilters.get(MetaWidget.VALUES, [])
        filters_type = prefilters.get(MetaWidget.FILTERS_TYPE, [])

        if any(len(lst) != len(property_models) for lst in [values, filters_type]):
            raise IllegalArgumentError(
                'The lists of "property_models", "values" and "filters_type" should be the '
                "same length."
            )
        prefilters = [
            PropertyValueFilter(
                property_model=pf[0],
                value=pf[1],
                filter_type=pf[2],
            )
            for pf in zip(property_models, values, filters_type)
        ]

        warnings.warn(
            "Prefilters must be provided as list of `PropertyValueFilter` objects. "
            "Separate input lists will be deprecated in January 2021.",  # TODO Deprecate January 2021
            PendingDeprecationWarning,
        )

    elif not all(isinstance(pf, PropertyValueFilter) for pf in prefilters):
        raise IllegalArgumentError(
            "`prefilters` must be a list of PropertyValueFilter objects."
        )

    if part_model:
        [pf.validate(part_model=part_model) for pf in prefilters]

    return prefilters


def _check_excluded_propmodels(
    part_model: "Part", property_models: List["AnyProperty"]
) -> List["AnyProperty"]:
    """
    Validate the excluded property models of the referenced part.

    :param part_model: Part model that is referenced
    :param property_models: Properties of the part model to be excluded.
    :return: list of property IDs
    :rtype list
    :raises IllegalArgumentError: whenever the properties are not of category MODEL or do not belong to the part model.
    """
    from pykechain.models import Property
    from pykechain.models import Part

    if not part_model:
        # part model is unknown, only check for property_models
        return [check_base(pm, Property, "property_model") for pm in property_models]

    if not isinstance(part_model, Part):
        raise IllegalArgumentError(
            f'`part_model` must be a Part object, "{part_model}" is not.'
        )

    list_of_propmodels_excl: List["AnyProperty"] = list()
    for property_model in property_models:
        if is_uuid(property_model):
            property_model = part_model.property(property_model)
        elif not isinstance(property_model, Property):
            raise IllegalArgumentError(
                "A part reference property can only exclude `Property` models or their UUIDs, "
                'found type "{}"'.format(type(property_model))
            )

        if property_model.category != Category.MODEL:
            raise IllegalArgumentError(
                "A part reference property can only exclude `Property` models, found "
                'category "{}" on property "{}"'.format(
                    property_model.category, property_model.name
                )
            )
        elif part_model.id != property_model.part_id:
            raise IllegalArgumentError(
                "A part reference property can only exclude properties belonging to the referenced"
                ' Part model, found referenced Part model "{}" and Properties belonging to "{}"'.format(
                    part_model.name, property_model.part.name
                )
            )
        else:
            list_of_propmodels_excl.append(property_model.id)
    return list_of_propmodels_excl

import datetime
import warnings
from abc import abstractmethod
from typing import Text, Union, Any, Dict, List, Optional

from pykechain.enums import FilterType, Category, PropertyType, ScopeStatus
from pykechain.exceptions import IllegalArgumentError, NotFoundError
from pykechain.models.input_checks import check_base, check_enum, check_type, check_text, check_datetime
from pykechain.models.widgets.enums import MetaWidget


class BaseFilter(object):
    """Base class for any filters used in pykechain."""

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return self.__class__.write_options(filters=[self]) == self.__class__.write_options(filters=[other])
        else:
            return False

    @classmethod
    @abstractmethod
    def parse_options(cls, options: Dict) -> List['BaseFilter']:  # pragma: no cover
        """
        Convert the dict & string-based definition of a filter to a list of Filter objects.

        :param options: options dict from a property or meta dict from a widget.
        :return: list of Filter objects
        :rtype list
        """
        pass

    @classmethod
    @abstractmethod
    def write_options(cls, filters: List) -> Dict:
        """
        Convert the list of Filter objects to a dict.

        :param filters: List of BaseFilter objects
        :returns options dict to be used to update the options dict of a property
        """
        if not all(isinstance(f, cls) for f in filters):
            raise IllegalArgumentError("All `filters` must be of type `{}`".format(cls))


class PropertyValueFilter(BaseFilter):
    """
    Property value filter, used for Part reference properties and filtered grid widgets.

    :ivar id: property model UUID
    :ivar value: value of the filter
    :ivar type: filter type
    """

    def __init__(
        self,
        property_model: Union[Text, 'Property'],
        value: Any,
        filter_type: FilterType,
    ):
        """Create PropertyValueFilter instance."""
        from pykechain.models import Property

        property_model_id = check_base(property_model, Property, "property_model")
        check_enum(filter_type, FilterType, "filter_type")

        self.id = property_model_id
        self.value = value
        self.type = filter_type

    def __repr__(self):
        return "PropertyValueFilter {}: {} ({})".format(self.type, self.value, self.id)

    def format(self) -> Text:
        """Format PropertyValueFilter as a string."""
        value = str(self.value).lower() if isinstance(self.value, bool) else self.value
        return "{}:{}:{}".format(self.id, value, self.type)

    def validate(self, part_model: 'Part') -> None:
        """
        Validate data of the PropertyValueFilter.

        :param part_model: Part model to which the filter will be applied.
        :returns None
        """
        from pykechain.models import Part

        check_base(part_model, Part, "part_model")

        try:
            prop = part_model.property(self.id)
        except NotFoundError:
            raise IllegalArgumentError(
                "Property value filters can only be set on properties belonging to the selected Part model.")

        if prop.category != Category.MODEL:
            raise IllegalArgumentError(
                'Property value filters can only be set on Property models, received "{}".'.format(prop))
        else:
            if prop.type == PropertyType.BOOLEAN_VALUE and self.type != FilterType.EXACT:
                warnings.warn("A PropertyValueFilter on a boolean property should use filter type `{}`".format(
                    FilterType.EXACT), Warning)

    @classmethod
    def parse_options(cls, options: Dict) -> List['PropertyValueFilter']:
        """
        Convert the dict & string-based definition of a property value filter to a list of PropertyValueFilter objects.

        :param options: options dict from a multi-reference property or meta dict from a filtered grid widget.
        :return: list of PropertyValueFilter objects
        :rtype list
        """
        check_type(options, dict, "options")

        prefilter_string = options.get(MetaWidget.PREFILTERS, {}).get("property_value")
        prefilter_string_list = prefilter_string.split(",") if prefilter_string else []

        prefilters = list()
        for pf_string in prefilter_string_list:
            prefilter_raw = pf_string.split(":")

            if len(prefilter_raw) == 1:   # FIXME encoding problem KE-chain
                prefilter_raw = pf_string.split("%3A")

            prefilters.append(PropertyValueFilter(*prefilter_raw))

        return prefilters

    @classmethod
    def write_options(cls, filters: List) -> Dict:
        """
        Convert the list of Filter objects to a dict.

        :param filters: List of BaseFilter objects
        :returns options dict to be used to update the options dict of a property
        """
        super().write_options(filters=filters)

        prefilters = {
            "property_value": ",".join([pf.format() for pf in filters])
        }
        options = {MetaWidget.PREFILTERS: prefilters}

        return options


class ScopeFilter(BaseFilter):
    """
    Scope filter, used on scope reference properties.

    :ivar tag: string
    """

    # map between KE-chain field and Pykechain attribute, and whether the filter is stored as a list (cs-string)
    MAP = [
        ("name__icontains", "name", False),
        ("status__in", "status", False),
        ("due_date__gte", "due_date_gte", False),
        ("due_date__lte", "due_date_lte", False),
        ("start_date__gte", "start_date_gte", False),
        ("start_date__lte", "start_date_lte", False),
        ("progress__gte", "progress_gte", False),
        ("progress__lte", "progress_lte", False),
        ("tags__contains", "tag", True),
        ("team__in", "team", False),
    ]

    def __init__(
            self,
            tag: Optional[Text] = None,
            status: Optional[ScopeStatus] = None,
            name: Optional[Text] = None,
            team: Optional[Union[Text, 'Team']] = None,
            due_date_gte: Optional[datetime.datetime] = None,
            due_date_lte: Optional[datetime.datetime] = None,
            start_date_gte: Optional[datetime.datetime] = None,
            start_date_lte: Optional[datetime.datetime] = None,
            progress_gte: Optional[float] = None,
            progress_lte: Optional[float] = None,
            **kwargs
    ):
        """Create a ScopeFilter object."""
        from pykechain.models import Team

        filters = [
            tag,
            status,
            name,
            team,
            due_date_gte,
            due_date_lte,
            start_date_gte,
            start_date_lte,
            progress_gte,
            progress_lte,
        ]
        if sum([p is not None for p in filters]) + len(kwargs) != 1:
            raise IllegalArgumentError("Every ScopeFilter object must apply only 1 filter!")

        self.status = check_enum(status, ScopeStatus, "status")
        self.name = check_text(name, "name")
        self.due_date_gte = check_datetime(due_date_gte, "due_date_gte")
        self.due_date_lte = check_datetime(due_date_lte, "due_date_lte")
        self.start_date_gte = check_datetime(start_date_gte, "start_date_gte")
        self.start_date_lte = check_datetime(start_date_lte, "start_date_lte")
        self.progress_gte = check_type(progress_gte, float, "progress_gte")
        self.progress_lte = check_type(progress_lte, float, "progress_lte")
        self.tag = check_text(tag, "tag")
        self.team = check_base(team, Team, "team")
        self.extra_filter: dict = kwargs

    def __repr__(self):
        _repr = "ScopeFilter: "
        if self.name:
            _repr += "name: `{}`".format(self.name)
        elif self.status:
            _repr += "status `{}`".format(self.status)
        elif self.due_date_gte:
            _repr += "due date greater or equal than: `{}`".format(self.due_date_gte)
        elif self.due_date_lte:
            _repr += "due date lesser or equal than: `{}`".format(self.due_date_lte)
        elif self.start_date_gte:
            _repr += "start date greater or equal than: `{}`".format(self.start_date_gte)
        elif self.start_date_lte:
            _repr += "start date lesser or equal than: `{}`".format(self.start_date_lte)
        elif self.progress_gte:
            _repr += "progress greater or equal than: {}%".format(self.progress_gte * 100)
        elif self.progress_lte:
            _repr += "progress lesser or equal than: {}%".format(self.progress_lte * 100)
        elif self.tag:
            _repr += "tag `{}`".format(self.tag)
        elif self.team:
            _repr += "team: `{}`".format(self.team)
        else:
            _repr += "{}".format(self.extra_filter)

        return _repr

    @classmethod
    def parse_options(cls, options: Dict) -> List['ScopeFilter']:
        """
        Convert the dict & string-based definition of a scope filter to a list of ScopeFilter objects.

        :param options: options dict from a scope reference property or meta dict from a scopes widget.
        :return: list of ScopeFilter objects
        :rtype list
        """
        check_type(options, dict, "options")

        filters_dict = options.get(MetaWidget.PREFILTERS, {})
        scope_filters = []

        mapping = {field: (attr, is_list) for field, attr, is_list in cls.MAP}

        for field, value in filters_dict.items():
            if field in mapping:
                attr, is_list = mapping[field]

                try:
                    if is_list:
                        values = value.split(",")
                    else:
                        values = [value]
                except AttributeError:
                    values = value

                for item in values:
                    scope_filters.append(cls(**{attr: item}))
            else:
                scope_filters.append(cls(**{field: value}))

        return scope_filters

    @classmethod
    def write_options(cls, filters: List) -> Dict:
        """
        Convert the list of Filter objects to a dict.

        :param filters: List of BaseFilter objects
        :returns options dict to be used to update the options dict of a property
        """
        super().write_options(filters=filters)

        prefilters = dict()
        options = {MetaWidget.PREFILTERS: prefilters}

        for f in filters:  # type: cls
            found = False
            for field, attr, is_list in cls.MAP:
                filter_value = getattr(f, attr)

                if filter_value is not None:
                    if is_list:
                        # creata a string with commaseparted prefilters, the first item directly and
                        # consequent items with a ,
                        # TODO: refactor to create a list and then join them with a ','
                        if field not in prefilters:
                            prefilters[field] = filter_value
                        else:
                            prefilters[field] += ",{}".format(filter_value)
                    else:
                        prefilters[field] = filter_value

                    found = True
                    break

            if not found:
                prefilters.update(f.extra_filter)

        return options

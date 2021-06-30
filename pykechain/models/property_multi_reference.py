import warnings
from typing import List, Optional, Text, Union, Any, Tuple

from pykechain.defaults import PARTS_BATCH_LIMIT
from pykechain.enums import Category, FilterType
from pykechain.models.base_reference import _ReferencePropertyInScope
from pykechain.models.input_checks import check_type
from pykechain.models.part import Part
from pykechain.models.value_filter import PropertyValueFilter
from pykechain.models.widgets.enums import MetaWidget
from pykechain.models.widgets.helpers import _check_prefilters, _check_excluded_propmodels
from pykechain.utils import get_in_chunks


class MultiReferenceProperty(_ReferencePropertyInScope):
    """A virtual object representing a KE-chain multi-references property.

    .. versionadded:: 1.14
    """

    REFERENCED_CLASS = Part

    def _retrieve_objects(self, **kwargs) -> List[Part]:
        """
        Retrieve a list of Parts.

        :param kwargs: optional inputs
        :return: list of Part objects
        """
        part_ids = self._validate_values()

        parts = []

        if part_ids:
            if self.category == Category.MODEL:
                parts = [self._client.part(pk=part_ids[0], category=None)]
            elif self.category == Category.INSTANCE:
                # Retrieve the referenced model for low-permissions scripts to enable use of the `id__in` key
                if False:  # TODO Check for script permissions in order to skip the model() retrieval
                    models = [None]
                else:
                    models = self.model().value
                if models:
                    parts = list()
                    for chunk in get_in_chunks(part_ids, PARTS_BATCH_LIMIT):
                        parts.extend(
                            list(self._client.parts(
                                id__in=','.join(chunk),
                                model=models[0],
                                category=None,
                            ))
                        )
        return parts

    def choices(self) -> List[Part]:
        """Retrieve the parts that you can reference for this `MultiReferenceProperty`.

        This method makes 2 API calls: 1) to retrieve the referenced model, and 2) to retrieve the instances of
        that model.

        :return: the :class:`Part`'s that can be referenced as a :class:`~pykechain.model.PartSet`.
        :raises APIError: When unable to load and provide the choices

        Example
        -------
        >>> reference_property = project.part('Bike').property('a_multi_reference_property')
        >>> referenced_part_choices = reference_property.choices()

        """
        possible_choices = list()
        # Check whether the model of this reference property (possible itself) has a configured value
        if self.model().has_value():
            # If a model is configured, retrieve its ID
            choices_model_id = self.model()._value[0].get('id')

            # Determine which parts are filtered out
            prefilter: Optional[Text] = self._options.get(MetaWidget.PREFILTERS, {}). \
                get(MetaWidget.PROPERTY_VALUE_PREFILTER)

            # Retrieve all part instances with this model ID
            possible_choices = self._client.parts(
                model_id=choices_model_id,
                property_value=prefilter,
            )

        return possible_choices

    def set_prefilters(
            self,
            property_models: List[Union[Text, 'AnyProperty']] = None,
            values: List[Any] = None,
            filters_type: List[FilterType] = None,
            prefilters: List[PropertyValueFilter] = None,
            overwrite: Optional[bool] = False,
            clear: Optional[bool] = False,
            validate: Optional[Union[bool, Part]] = True,
    ) -> None:
        """
        Set the pre-filters on a `MultiReferenceProperty`.

        :param property_models: `list` of `Property` models (or their IDs) to set pre-filters on
        :type property_models: list
        :param values: `list` of values to pre-filter on, value has to match the property type.
        :type values: list
        :param filters_type: `list` of filter types per pre-filter, one of :class:`enums.FilterType`,
                defaults to `FilterType.CONTAINS`
        :type filters_type: list
        :param prefilters: `list` of PropertyValueFilter objects
        :type prefilters: list
        :param overwrite: whether existing pre-filters should be overwritten, if new filters to the same property
            are provided as input. Does not remove non-conflicting prefilters. (default = False)
        :type overwrite: bool
        :param clear: whether all existing pre-filters should be cleared. (default = False)
        :type clear: bool
        :param validate: whether the pre-filters are validated to the referenced model, which can be provided as well
        :type validate: bool

        :raises IllegalArgumentError: when the type of the input is provided incorrect.
        """
        if not clear:
            list_of_prefilters = PropertyValueFilter.parse_options(options=self._options)
        else:
            list_of_prefilters = list()

        if prefilters is None:
            new_prefilters = {
                "property_models": property_models,
                "values": values,
                "filters_type": filters_type,
            }
        else:
            new_prefilters = prefilters

        if not validate:
            part_model = None
        elif isinstance(validate, Part):
            part_model = validate
        else:
            part_model = self.value[0]

        verified_prefilters = _check_prefilters(
            part_model=part_model,
            prefilters=new_prefilters,
        )

        if overwrite:  # Remove pre-filters from the existing prefilters if they match the property model UUID
            provided_filter_ids = {pf.id for pf in verified_prefilters}
            list_of_prefilters = [pf for pf in list_of_prefilters if pf.id not in provided_filter_ids]

        list_of_prefilters += verified_prefilters

        # Only update the options if there are any prefilters to be set, or if the original filters have to overwritten
        if list_of_prefilters or clear:
            self._options.update(
                PropertyValueFilter.write_options(filters=list_of_prefilters)
            )
            self.edit(options=self._options)

    def get_prefilters(
            self,
            as_lists: Optional[bool] = False,
    ) -> Union[
        List[PropertyValueFilter],
        Tuple[List[Text]]
    ]:
        """
        Retrieve the pre-filters applied to the reference property.

        :param as_lists: (O) (default = False)
            If True, the pre-filters are returned as three lists of property model UUIDs, values and filter types.
        :return: prefilters
        """
        check_type(as_lists, bool, "as_lists")

        prefilters = PropertyValueFilter.parse_options(options=self._options)

        if as_lists:
            property_model_ids = [pf.id for pf in prefilters]
            values = [pf.value for pf in prefilters]
            filter_types = [pf.type for pf in prefilters]
            prefilters = tuple([property_model_ids, values, filter_types])

            warnings.warn(
                "Prefilters will be provided as list of `PropertyValueFilter` objects. "
                "Separate lists will be deprecated in January 2021.",  # TODO Deprecate January 2021
                PendingDeprecationWarning,
            )

        return prefilters

    def set_excluded_propmodels(
            self,
            property_models: List[Union[Text, 'AnyProperty']],
            overwrite: Optional[bool] = False,
            validate: Optional[Union[bool, Part]] = True,
    ) -> None:
        """
        Exclude a list of properties from being visible in the part-shop and modal (pop-up) of the reference property.

        :param property_models: `list` of Property models (or their IDs) to exclude.
        :type property_models: list
        :param overwrite: flag whether to overwrite existing (True) or append (False, default) to existing filter(s).
        :type overwrite bool
        :param validate: whether the pre-filters are validated to the referenced model, which can be provided as well
        :type validate: bool

        :raises IllegalArgumentError
        """
        if not overwrite:
            list_of_propmodels_excl = self._options.get('propmodels_excl', [])
        else:
            list_of_propmodels_excl = list()

        if not validate:
            part_model = None
        elif isinstance(validate, Part):
            part_model = validate
        else:
            part_model = self.value[0]

        list_of_propmodels_excl.extend(_check_excluded_propmodels(
            part_model=part_model,
            property_models=property_models,
        ))

        options_to_set = self._options
        options_to_set['propmodels_excl'] = list(set(list_of_propmodels_excl))

        self.edit(options=options_to_set)

    def get_excluded_propmodel_ids(self) -> List[Text]:
        """
        Retrieve a list of property model UUIDs which are not visible.

        :return: list of UUIDs
        :rtype list
        """
        return self._options.get("propmodels_excl", [])

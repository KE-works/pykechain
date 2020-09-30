from typing import List, Optional, Text, Union, Any

from pykechain.enums import Category, FilterType
from pykechain.models.property2_multi_reference import MultiReferenceProperty2
from pykechain.models.base_reference import _ReferencePropertyInScope
from pykechain.models.part import Part
from pykechain.models.widgets.helpers import _check_prefilters, _check_excluded_propmodels


class MultiReferenceProperty(_ReferencePropertyInScope, MultiReferenceProperty2):
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
                    parts = list(self._client.parts(
                        id__in=','.join(part_ids),
                        model=models[0],
                        category=None,
                    ))
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
            prefilter = self._options.get('prefilters', {}).get('property_value')  # type: Optional[Text]

            # Retrieve all part instances with this model ID
            possible_choices = self._client.parts(
                model_id=choices_model_id,
                property_value=prefilter,
            )

        return possible_choices

    def set_prefilters(
            self,
            property_models: List[Union[Text, 'AnyProperty']],
            values: List[Any],
            filters_type: List[FilterType],
            overwrite: Optional[bool] = False
    ) -> None:
        """
        Set the pre-filters on a `MultiReferenceProperty`.

        :param property_models: `list` of `Property` models (or their IDs) to set pre-filters on
        :type property_models: list
        :param values: `list` of values to pre-filter on, value has to match the property type.
        :type values: list
        :param filters_type: `list` of filter types per pre-fitler, one of :class:`enums.FilterType`,
                defaults to `FilterType.CONTAINS`
        :type filters_type: list
        :param overwrite: determines whether the pre-filters should be over-written or not, defaults to False
        :type overwrite: bool

        :raises IllegalArgumentError: when the type of the input is provided incorrect.
        """
        if not overwrite:
            initial_prefilters = self._options.get('prefilters', {})
            prefilter_string = initial_prefilters.get('property_value', '')
            list_of_prefilters = prefilter_string.split(',') if prefilter_string else []
        else:
            list_of_prefilters = list()

        new_prefilters = {
            'property_models': property_models,
            'values': values,
            'filters_type': filters_type,
        }

        list_of_prefilters.extend(_check_prefilters(
            part_model=self.value[0],
            prefilters=new_prefilters,
        ))

        # Only update the options if there are any prefilters to be set, or if the original filters have to overwritten
        if list_of_prefilters or overwrite:
            options_to_set = self._options

            # Always create the entire prefilter json structure
            options_to_set['prefilters'] = {
                'property_value': ','.join(list_of_prefilters) if list_of_prefilters else ""
            }

            self.edit(options=options_to_set)

    def set_excluded_propmodels(
            self,
            property_models: List[Union[Text, 'AnyProperty']],
            overwrite: Optional[bool] = False,
    ) -> None:
        """
        Exclude a list of properties from being visible in the part-shop and modal (pop-up) of the reference property.

        :param property_models: `list` of Property models (or their IDs) to exclude.
        :type property_models: list
        :param overwrite: flag whether to overwrite existing (True) or append (False, default) to existing filter(s).
        :type overwrite bool

        :raises IllegalArgumentError
        """
        if not overwrite:
            list_of_propmodels_excl = self._options.get('propmodels_excl', [])
        else:
            list_of_propmodels_excl = list()

        list_of_propmodels_excl.extend(_check_excluded_propmodels(
            part_model=self.value[0],
            property_models=property_models,
        ))

        options_to_set = self._options
        options_to_set['propmodels_excl'] = list_of_propmodels_excl

        self.edit(options=options_to_set)

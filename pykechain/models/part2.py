from typing import Any  # noqa: F401

import requests
from six import text_type

from pykechain.enums import Category
from pykechain.exceptions import APIError, IllegalArgumentError, NotFoundError
from pykechain.models import Part
from pykechain.models.property2 import Property2
from pykechain.utils import is_uuid


class Part2(Part):
    """A virtual object representing a KE-chain part.

    :cvar basestring category: The category of the part, either 'MODEL' or 'INSTANCE'
                               (use :class:`pykechain.enums.Category`)
    :cvar basestring parent_id: The UUID of the parent of this part
    :cvar properties: The list of :class:`Property` objects belonging to this part.
    :cvar basestring multiplicity: The multiplicity of the part being one of the following options:
                                   ZERO_ONE, ONE, ZERO_MANY, ONE_MANY, (reserved) M_N

    Examples
    --------
    For the category property

    >>> bike = project.part('Bike')
    >>> bike.category
    'INSTANCE'

    >>> bike_model = project.model('Bike')
    >>> bike_model.category
    'MODEL'

    >>> bike_model == Category.MODEL
    True
    >>> bike == Category.INSTANCE
    True

    For the multiplicity property

    >>> bike = project.models('Bike')
    >>> bike.multiplicity
    ONE_MANY

    >>> from pykechain.enums import Multiplicity
    >>> bike.multiplicity == Multiplicity.ONE_MANY
    True

    """

    def __init__(self, json, **kwargs):
        # type: (dict, **Any) -> None
        """Construct a part from a KE-chain 2 json response.

        :param json: the json response to construct the :class:`Part` from
        :type json: dict
        """
        # we need to run the init of 'Base' instead of 'Part' as we do not need the instantiation of properties
        super(Part, self).__init__(json, **kwargs)

        self.category = json.get('category')
        self.parent_id = json.get('parent_id', None)
        self.multiplicity = json.get('multiplicity', None)
        self._cached_children = None

        self.properties = [Property2.create(p, client=self._client) for p in json['properties']]

    def refresh(self, json=None, url=None, extra_params=None):
        """Refresh the object in place."""
        from pykechain.client import API_EXTRA_PARAMS
        super(Part2, self).refresh(json=json,
                                   url=self._client._build_url('part2', part_id=self.id),
                                   extra_params=API_EXTRA_PARAMS['part2'])

    def model(self):
        """
        Retrieve the model of this `Part` as `Part`.

        For instance, you can get the part model of a part instance. But trying to get the model of a part that
        has no model, like a part model, will raise a :exc:`NotFoundError`.

        .. versionadded:: 1.8

        :return: the model of this part instance as :class:`Part` with category `MODEL`
        :raises NotFoundError: if no model found

        Example
        -------
        >>> front_fork = project.part('Front Fork')
        >>> front_fork_model = front_fork.model()

        """
        if self.category == Category.INSTANCE:
            model_id = self._json_data.get('model_id')
            return self._client.model(pk=model_id)
        else:
            raise NotFoundError("Part {} has no model".format(self.name))

    def edit(self, name=None, description=None, **kwargs):
        """Edit the details of a part (model or instance).

        For an instance you can edit the Part instance name and the part instance description. To alter the values
        of properties use :func:`Part.update()`.

        In order to prevent the backend from updating the frontend you may add `suppress_kevents=True` as
        additional keyword=value argument to this method. This will improve performance of the backend
        against a trade-off that someone looking at the frontend won't notice any changes unless the page
        is refreshed.

        :param name: optional name of the part to edit
        :param description: (optional) description of the part
        :type description: basestring or None
        :param kwargs: (optional) additional kwargs that will be passed in the during the edit/update request
        :type kwargs: dict or None
        :return: the updated object if successful
        :raises IllegalArgumentError: when the type or value of an argument provided is incorrect
        :raises APIError: in case an Error occurs

        Example
        -------

        For changing a part:

        >>> front_fork = project.part('Front Fork')
        >>> front_fork.edit(name='Front Fork - updated')
        >>> front_fork.edit(name='Front Fork cruizer', description='With my ragtop down so my hair can blow' )

        for changing a model:

        >>> front_fork = project.model('Front Fork')
        >>> front_fork.edit(name='Front Fork basemodel', description='Some description here')

        """
        update_dict = {'id': self.id}
        if name is not None:
            if not isinstance(name, text_type):
                raise IllegalArgumentError("name should be provided as a string")
            update_dict.update({'name': name})
        if description is not None:
            if not isinstance(description, text_type):
                raise IllegalArgumentError("description should be provided as a string")
            update_dict.update({'description': description})

        if kwargs is not None:  # pragma: no cover
            update_dict.update(**kwargs)

        from pykechain.client import API_EXTRA_PARAMS
        response = self._client._request('PUT',
                                  self._client._build_url('part2', part_id=self.id),
                                  params=API_EXTRA_PARAMS['part2'],
                                  json=update_dict)

        if response.status_code != requests.codes.ok:  # pragma: no cover
            raise APIError("Could not update Part ({})".format(response))

        if name:
            self.name = name

    def add_with_properties(self, model, name=None, update_dict=None, properties_fvalues=None, refresh=True, **kwargs):
        """
        Add a part as a child of this part and update its properties in one go.

        In order to prevent the backend from updating the frontend you may add `suppress_kevents=True` as
        additional keyword=value argument to this method. This will improve performance of the backend
        against a trade-off that someone looking at the frontend won't notice any changes unless the page
        is refreshed.

        With KE-chain 3 backends you may now provide a whole set of properties to update using a `properties_fvalues`
        list of dicts. This will be merged with the `update_dict` optionally provided.
        The `properties_fvalues` list is a list of dicts containing at least the `id` and a `value`, but other keys
        may provided as well in the single update eg. `value_options`. Example::
            `properties_fvalues = [ {"id":<uuid of prop>, "value":<new_prop_value>}, {...}, ...]`

        .. versionchanged:: 3.0
           Added compatibility with KE-chain 3 backend. You may provide properties_fvalues as kwarg.
           Bulk option removed.

        :param model: model of the part which to add a new instance, should follow the model tree in KE-chain
        :type model: :class:`Part`
        :param name: (optional) name provided for the new instance as string otherwise use the name of the model
        :type name: basestring or None
        :param update_dict: dictionary with keys being property names (str) or property_id (from the property models)
                            and values being property values
        :type update_dict: dict or None
        :param properties_fvalues: (optional) keyword argument with raw list of properties update dicts
        :type properties_fvalues: list of dict or None
        :param refresh: refresh the part after succesfull completion, default to True
        :type refresh: bool
        :param kwargs: (optional) additional keyword arguments that will be passed inside the update request
        :type kwargs: dict or None
        :return: the newly created :class:`Part`
        :raises NotFoundError: when the property name is not a valid property of this part
        :raises APIError: in case an Error occurs
        :raised IllegalArgumentError: in case of illegal arguments.

        Examples
        --------
        >>> bike = client.scope('Bike Project').part('Bike')
        >>> wheel_model = client.scope('Bike Project').model('Wheel')
        >>> bike.add_with_properties(wheel_model, 'Wooden Wheel', {'Spokes': 11, 'Material': 'Wood'})

        """
        if self.category != Category.INSTANCE:
            raise APIError("Part should be of category INSTANCE")

        if properties_fvalues and not isinstance(properties_fvalues, list):
            raise IllegalArgumentError("optional `properties_fvalues` need to be provided as a list of dicts")

        name = name or model.name
        url = self._client._build_url('parts2_new_instance')

        properties_fvalues = properties_fvalues or list()

        for prop_name_or_id, property_value in update_dict.items():
            updated_p = dict(
                value=property_value
            )
            if is_uuid(prop_name_or_id):
                updated_p['model_id'] = prop_name_or_id
            else:
                updated_p['model_id'] = model.property(prop_name_or_id).id
            properties_fvalues.append(updated_p)

        from pykechain.client import API_EXTRA_PARAMS
        response = self._client._request(
            'POST', url,
            params=API_EXTRA_PARAMS['parts2'],
            json=dict(
                name=name,
                model_id=model.id,
                parent_id=self.id,
                properties_fvalues=properties_fvalues,
                **kwargs
            )
        )

        if response.status_code != requests.codes.created:  # pragma: no cover
            raise APIError('{}: {}'.format(str(response), response.content))

        # ensure that cached children are reset such that next call the children are refreshed
        self._cached_children = None
        if refresh:
            self.children()

        return Part2(response.json()['results'][0], client=self._client)

        # else:  # do the old way
        #     new_part = self.add(model, name=name)  # type: Part
        #     new_part.update(update_dict=update_dict, bulk=bulk)
        #     return new_part

    def update(self, name=None, update_dict=None, properties_fvalues=None, refresh=True, **kwargs):
        """
        Edit part name and property values in one go.

        In order to prevent the backend from updating the frontend you may add `suppress_kevents=True` as
        additional keyword=value argument to this method. This will improve performance of the backend
        against a trade-off that someone looking at the frontend won't notice any changes unless the page
        is refreshed.

        With KE-chain 3 backends you may now provide a whole set of properties to update using a `properties_fvalues`
        list of dicts. This will be merged with the `update_dict` optionally provided.
        The `properties_fvalues` list is a list of dicts containing at least the `id` and a `value`, but other keys
        may provided as well in the single update eg. `value_options`. Example::
            `properties_fvalues = [ {"id":<uuid of prop>, "value":<new_prop_value>}, {...}, ...]`

        .. versionchanged:: 3.0
           Added compatibility with KE-chain 3 backend. You may provide properties_fvalues as kwarg.
           Bulk option removed.

        :param name: new part name (defined as a string)
        :type name: basestring or None
        :param update_dict: dictionary with keys being property names (str) or property ids (uuid)
                            and values being property values
        :type update_dict: dict or None
        :param properties_fvalues: (optional) keyword argument with raw list of properties update dicts
        :type properties_fvalues: list of dict or None
        :param refresh: refresh the part after succesfull completion, default to True
        :type refresh: bool
        :param kwargs: additional keyword-value arguments that will be passed into the part update request.
        :type kwargs: dict or None

        :return: the updated :class:`Part`
        :raises NotFoundError: when the property name is not a valid property of this part
        :raises IllegalArgumentError: when the type or value of an argument provided is incorrect
        :raises APIError: in case an Error occurs

        Example
        -------

        >>> bike = project.part('Bike')
        >>> bike.update(name='Good name', update_dict={'Gears': 11, 'Total Height': 56.3})

        Example with properties_fvalues: <pyke Part2 'Copied model under Bike' id 95d35be6>

        >>> bike = project.part('Bike')
        >>> bike.update(name='Good name',
        ...             properties_fvalues=[{'id': '95d35be6...', 'value': 11},
        ...                                 {'id': '7893cba4...', 'value': 56.3, 'value_options': {...}})

        """
        # dict(name=name, properties=json.dumps(update_dict))) with property ids:value
        # action = 'bulk_update_properties'  # not for KEC3
        if name and not isinstance(name, text_type):
            raise IllegalArgumentError("Name of the part should be provided as a string")

        if properties_fvalues and not isinstance(properties_fvalues, list):
            raise IllegalArgumentError("optional `properties_fvalues` need to be provided as a list of dicts")

        properties_fvalues = properties_fvalues or list()
        update_dict = update_dict or dict()

        for prop_name_or_id, property_value in update_dict.items():
            updated_p = dict(
                value=property_value
            )
            if is_uuid(prop_name_or_id):
                updated_p['id'] = prop_name_or_id
            else:
                updated_p['id'] = self.property(prop_name_or_id).id
            properties_fvalues.append(updated_p)

        payload_json = dict(
            properties_fvalues=properties_fvalues,
            **kwargs
        )

        if name:
            payload_json.update(name=name)

        from pykechain.client import API_EXTRA_PARAMS
        response = self._client._request(
            'PUT', self._client._build_url('part2', part_id=self.id),
            params=API_EXTRA_PARAMS['part2'],
            json=payload_json
        )

        if response.status_code != requests.codes.ok:  # pragma: no cover
            raise APIError("Could not update the part '{}', got: '{}'".format(self, response.content))

        # update local properties (without a call)
        self.refresh(json=response.json()['results'][0])
        # self.properties = [Property2.create(p, client=self._client) for p in self._json_data['properties']]

    def delete(self):
        # type: () -> None
        """Delete this part.

        :return: None
        :raises APIError: in case an Error occurs
        """
        response = self._client._request('DELETE', self._client._build_url('part2', part_id=self.id))

        if response.status_code != requests.codes.no_content:  # pragma: no cover
            raise APIError("Could not delete part: {} with id {}: ({})".format(self.name, self.id, response))

    def order_properties(self, property_list=None):
        """
        Order the properties of a part model using a list of property objects or property names or property id's.

        For KE-chain 3 backends, the order can also directly provided as a unique integer for each property in the
        `Part.update()` function if you provide the `properties_fvalues` list of dicts yourself. For more information
        please refer to the `Part2.update()` documentation.

        .. versionchanged:: 3.0
           For KE-chain 3 backend the `Part.update()` method is used with a properties_fvalues list of dicts.

        :param property_list: ordered list of property names (basestring) or property id's (uuid) or
                              a `Property` object.
        :type property_list: list(basestring)
        :returns: the :class:`Part` with the reordered list of properties
        :raises APIError: when an Error occurs
        :raises IllegalArgumentError: When provided a wrong argument

        Examples
        --------
        >>> front_fork = project.model('Front Fork')
        >>> front_fork.order_properties(['Material', 'Height (mm)', 'Color'])

        >>> front_fork = project.model('Front Fork')
        >>> material = front_fork.property('Material')
        >>> height = front_fork.property('Height (mm)')
        >>> color = front_fork.property('Color')
        >>> front_fork.order_properties([material, height, color])

        Alternatively you may use the `Part.update()` function to directly alter the order of the properties and
        eventually even more (defaut) model values.

        >>> front_fork.update(properties_fvalues= [{'id': material.id, 'order':10},
        ...                                        {'id': height.id, 'order': 20, 'value':13.37}
        ...                                        {'id': color.id, 'order':  30, 'name': 'Colour'}])

        """
        # in KEC3 backend we can (re)use the part update endpoint with a properties_fvalues list of dicts
        # properties_fvalues = [ {'model_id':<uuid>, 'order': <int> ]

        if self.category != Category.MODEL:
            raise APIError("Part should be of category MODEL")
        if not isinstance(property_list, list):
            raise IllegalArgumentError('Expected a list of strings or Property() objects, got a {} object'.
                                       format(type(property_list)))

        properties_fvalues = list()
        for order, prop_name_or_id in enumerate(property_list):
            updated_p = {'order': order}
            if is_uuid(prop_name_or_id):
                updated_p['id'] = prop_name_or_id
            elif isinstance(prop_name_or_id, Property2):
                updated_p['id'] = prop_name_or_id.id
            else:
                updated_p['id'] = self.property(prop_name_or_id).id
            properties_fvalues.append(updated_p)

        return self.update(properties_fvalues=properties_fvalues)

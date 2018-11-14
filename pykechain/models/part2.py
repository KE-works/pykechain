from typing import Any  # noqa: F401

import requests

from pykechain.enums import Multiplicity, Category
from pykechain.exceptions import APIError, IllegalArgumentError, NotFoundError
from pykechain.models import Part
from pykechain.models.property2 import Property2


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
        super(Part, self).__init__(json, **kwargs)

        self.category = json.get('category')
        self.parent_id = json.get('parent_id', None)
        self.multiplicity = json.get('multiplicity', None)
        self._cached_children = None

        self.properties = [Property2.create(p, client=self._client) for p in json['properties']]

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
        # type: (AnyStr, AnyStr, **Any) -> None
        """
        Edit the details of a part (model or instance).

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
        if name:
            if not isinstance(name, str):
                raise IllegalArgumentError("name should be provided as a string")
            update_dict.update({'name': name})
        if description:
            if not isinstance(description, str):
                raise IllegalArgumentError("description should be provided as a string")
            update_dict.update({'description': description})

        if kwargs:  # pragma: no cover
            update_dict.update(**kwargs)

        from pykechain.client import API_EXTRA_PARAMS
        r = self._client._request('PUT',
                                  self._client._build_url('part2', part_id=self.id),
                                  params=API_EXTRA_PARAMS['part2'],
                                  json=update_dict)

        if r.status_code != requests.codes.ok:  # pragma: no cover
            raise APIError("Could not update Part ({})".format(r))

        if name:
            self.name = name

    def delete(self):
        # type: () -> None
        """Delete this part.

        :return: None
        :raises APIError: in case an Error occurs
        """
        response = self._client._request('DELETE', self._client._build_url('part2', part_id=self.id))

        if response.status_code != requests.codes.no_content:  # pragma: no cover
            raise APIError("Could not delete part: {} with id {}: ({})".format(self.name, self.id, response))

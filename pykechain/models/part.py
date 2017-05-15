import json

import requests
from typing import Any, AnyStr  # flake8: noqa

from pykechain.enums import Multiplicity, Category
from pykechain.exceptions import NotFoundError, APIError
from pykechain.models.base import Base
from pykechain.models.property import Property
from pykechain.utils import find


class Part(Base):
    """A virtual object representing a KE-chain part.

    :cvar category: The category of the part, either 'MODEL' or 'INSTANCE' (use `pykechain.enums.Category`)
    :cvar parent_id: The UUID of the parent of this part
    :cvar properties: The list of `pykechain.models.Property` objects belonging to this part.

    """

    def __init__(self, json, **kwargs):
        # type: (dict, **Any) -> None
        """Construct a part from provided json data."""
        super(Part, self).__init__(json, **kwargs)

        self.category = json.get('category')
        self.parent_id = json['parent'].get('id') if 'parent' in json and json.get('parent') else None
        self.properties = [Property.create(p, client=self._client) for p in json['properties']]

    def property(self, name):
        # type: (str) -> Property
        """Retrieve the property with name belonging to this part.

        If you need to retrieve the property using eg. the id, use :meth:`pykechain.Client.properties`.

        :param name: property name to search for
        :return: a single :class:`pykechain.models.Property`
        :raises: NotFoundError

        Example
        -------

        >>> part = project.part('Bike')
        >>> part.properties
        [<pyke Property ...>, ...]
        # this returns a list of all properties of this part
        
        >>> gears = part.property('Gears')
        >>> gears.value
        6
        """
        found = find(self.properties, lambda p: name == p.name)

        if not found:
            raise NotFoundError("Could not find property with name {}".format(name))

        return found

    def parent(self):
        # type: () -> Any
        """Retrieve the parent of this `Part`.

        :return: the parent `Part`s as :class:`pykechain.model.Part`.
        :raises: APIError

        Example
        -------

        >>> part = project.part('Frame')
        >>> bike = part.parent()

        """
        if self.parent_id:
            return self._client.part(pk=self.parent_id, category=self.category)
        else:
            return None

    def children(self):
        # type: () -> Any
        """Retrieve the children of this `Part` as `Partset`.

        :return: a set of `Part`s as :class:`pykechain.model.PartSet`. Will be empty if no children
        :raises: APIError

        Example
        -------

        >>> bike = project.part('Bike')
        >>> direct_descendants_of_bike = bike.children()
        """
        return self._client.parts(parent=self.id, category=self.category)

    def siblings(self):
        # type: () -> Any
        """Retrieve the siblings of this `Part` as `Partset`.

        Siblings are other Parts sharing the same parent of this `Part`

        :return: a set of `Part`s as :class:`pykechain.model.PartSet`. Will be empty if no siblings
        :raises: APIError
        """
        if self.parent_id:
            return self._client.parts(parent=self.parent_id, category=self.category)
        else:
            from pykechain.models.partset import PartSet
            return PartSet(parts=[])

    def model(self):
        """
        Retrieve the model of this `Part` as `Part`.

        For instance, you can get the part model of a part instance. But trying to get the model of a part that
        has no model, like a part model, will raise a NotFoundError.

        :return: pykechain.models.Part
        :raises: NotFoundError

        Example
        -------
        >>> front_fork = project.part('Front Fork')
        >>> front_fork_model = front_fork.model()

        """
        if self.category == Category.INSTANCE:
            model_id = self._json_data['model'].get('id')
            return self._client.model(pk=model_id)
        else:
            raise NotFoundError("Part {} has no model".format(self.name))

    def proxy_model(self):
        """
        Retrieve the proxy model of this proxied `Part` as a `Part`.

        Allows you to retrieve the model of a proxy. But trying to get the catalog model of a part that
        has is no proxy, will raise a NotFoundError. Only models can have a proxy.

        :return: pykechain.models.Part
        :raises: NotFoundError

        Example
        -------

        >>> proxy_part = project.model('Proxy based on catalog model')
        >>> catalog_model_of_proxy_part = proxy_part.proxy_model()

        >>> proxied_material_of_the_bolt_model = project.model('Bolt Material')
        >>> proxy_basis_for_the_material_model = proxied_material_of_the_bolt_model.proxy_model()

        """
        assert self.category == Category.MODEL, \
            "Part {} is not a model, therefore it cannot have a proxy model".format(self)
        if 'proxy' in self._json_data and self._json_data.get('proxy'):
            catalog_model_id = self._json_data['proxy'].get('id')
            return self._client.model(pk=catalog_model_id)
        else:
            raise NotFoundError("Part {} is not a proxy".format(self.name))

    def add(self, model, **kwargs):
        # type: (Part, **Any) -> Part
        """Add a new child to this part.

        This can only act on instances

        :param model: model to use for the child
        :return: :class:`pykechain.models.Part`
        :raises: APIError

        Example
        -------

        >>> bike = project.part('Bike')
        >>> wheel_model = project.model('Wheel')
        >>> bike.add(wheel_model)
        """
        assert self.category == Category.INSTANCE

        return self._client.create_part(self, model, **kwargs)

    def add_to(self, parent, **kwargs):
        # type: (Part, **Any) -> Part
        """Add a new instance of this model to a part.

        :param parent: part to add the new instance to
        :return: :class:`pykechain.models.Part`
        :raises: APIError
        
        Example
        -------
        
        >>> wheel_model = project.model('wheel')
        >>> bike = project.part('Bike')
        >>> wheel_model.add_to(bike)
        """
        assert self.category == Category.MODEL

        return self._client.create_part(parent, self, **kwargs)

    def add_model(self, *args, **kwargs):
        # type: (*Any, **Any) -> Part
        """Add a new child model to this model.

        See :class:`pykechain.Client.create_model` for available parameters.

        :return: Part
        """
        assert self.category == Category.MODEL

        return self._client.create_model(self, *args, **kwargs)

    def add_proxy_to(self, parent, name, multiplicity=Multiplicity.ONE_MANY):
        # type: (Any, AnyStr, Any) -> Part
        """Add this model as a proxy to another parent model.
        
        This will add the current model as a proxy model to another parent model. It ensure that it will copy the
        whole subassembly to the 'parent' model.
        
        :param name: Name of the new proxy model
        :param parent: parent of the 
        :param multiplicity: the multiplicity of the new proxy model (default ONE_MANY) 
        :return: Part (self)
        
        Examples
        --------
        >>> from pykechain.enums import Multiplicity
        >>> bike_model = project.model('Bike')
        # find the catalog model container, the highest parent to create catalog models under
        >>> catalog_model_container = project.model('Catalog container')
        >>> new_wheel_model = project.create_model(catalog_model_container, 'Wheel Catalog', 
        ...                                        multiplicity=Multiplicity.ZERO_MANY)
        >>> new_wheel_model.add_proxy_to(bike_model, "Wheel", multiplicity=Multiplicity.ONE_MANY)
        
        """
        return self._client.create_proxy_model(self, parent, name, multiplicity)

    def add_property(self, *args, **kwargs):
        # type: (*Any, **Any) -> Property
        """Add a new property to this model.

        See :class:`pykechain.Client.create_property` for available parameters.

        :return: Property
        """
        assert self.category == Category.MODEL

        return self._client.create_property(self, *args, **kwargs)

    def delete(self):
        # type: () -> None
        """Delete this part.

        :return: None
        :raises: APIError if delete was not succesfull
        """
        r = self._client._request('DELETE', self._client._build_url('part', part_id=self.id))

        if r.status_code != requests.codes.no_content:
            raise APIError("Could not delete part: {} with id {}".format(self.name, self.id))

    def edit(self, name=None, description=None):
        # type: (AnyStr, AnyStr) -> None
        """
        Edit the details of a part (model or instance).

        For an instance you can edit the Part instance name and the part instance description

        :param name: optional name of the part to edit
        :param description: optional description of the part
        :return: None
        :raises: APIError

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
            assert type(name) == str, "name should be provided as a string"
            update_dict.update({'name': name})
        if description:
            assert type(description) == str, "description should be provided as a string"
            update_dict.update({'description': description})
        r = self._client._request('PUT', self._client._build_url('part', part_id=self.id), json=update_dict)

        if r.status_code != requests.codes.ok:
            raise APIError("Could not update Part ({})".format(r))

        if name:
            self.name = name

    def _repr_html_(self):
        # type: () -> str

        html = [
            "<table width=100%>",
            "<caption>{}</caption>".format(self.name),
            "<tr>",
            "<th>Property</th>",
            "<th>Value</th>",
            "</tr>"
        ]

        for prop in self.properties:
            style = "color:blue;" if prop.output else ""

            html.append("<tr style=\"{}\">".format(style))
            html.append("<td>{}</td>".format(prop.name))
            html.append("<td>{}</td>".format(prop.value))
            html.append("</tr>")

        html.append("</table>")

        return ''.join(html)

    def update(self, update_dict=None, bulk=True):
        """
        Use a dictionary with property names and property values to update the properties belonging to this part.

        :param update_dict: dictionary with keys being property names (str) and values being property values
        :param bulk: True to use the bulk_update_properties API endpoint for KE-chain versions later then 2.1.0b
        :return: :class:`pykechain.models.Part`
        :raises: APIError, Raises `NotFoundError` when the property name is not a valid property of this part

        Example
        -------
        
        >>> bike = client.scope('Bike Project').part('Bike')
        >>> bike.update({'Gears': 11, 'Total Height': 56.3}, bulk=True)
        
        """
        # new for 1.5 and KE-chain 2 (released after 14 march 2017) is the 'bulk_update_properties' action on the api
        # lets first use this one.
        # dict(properties=json.dumps(update_dict))) with property ids:value
        action = 'bulk_update_properties'

        url = self._client._build_url('part', part_id=self.id)
        request_body = dict([(self.property(property_name).id, property_value)
                             for property_name, property_value in update_dict.items()])

        if bulk and len(update_dict.keys()) > 1:
            r = self._client._request('PUT', self._client._build_url('part', part_id=self.id),
                                      data=dict(properties=json.dumps(request_body)),
                                      params=dict(select_action=action))
            if r.status_code != requests.codes.ok:
                raise APIError('{}: {}'.format(str(r), r.content))
        else:
            for property_name, property_value in update_dict.items():
                self.property(property_name).value = property_value

    def add_with_properties(self, model, name=None, update_dict=None, bulk=True):
        """
        Add a part and update its properties in one go.
        
        :param model: model of the part which to add a new instance, should follow the model tree in KE-chain
        :param name: (optional) name provided for the new instance as string otherwise use the name of the model
        :param update_dict: dictionary with keys being property names (str) and values being property values
        :param bulk: True to use the bulk_update_properties API endpoint for KE-chain versions later then 2.1.0b
        :return: :class:`pykechain.models.Part`
        :raises: APIError, Raises `NotFoundError` when the property name is not a valid property of this part

        Examples
        --------
        >>> bike = client.scope('Bike Project').part('Bike')
        >>> wheel_model = client.scope('Bike Project').model('Wheel') 
        >>> bike.add_with_properties(wheel_model, 'Wooden Wheel', {'Spokes': 11, 'Material': 'Wood'})
        
        """
        # TODO: add test coverage for this method
        assert self.category == Category.INSTANCE
        name = name or model.name
        action = 'new_instance_with_properties'

        properties_update_dict = dict([(model.property(property_name).id, property_value)
                                       for property_name, property_value in update_dict.items()])
        # TODO: add bulk = False flags such that is used the old API (sequential)
        if bulk:
            r = self._client._request('POST', self._client._build_url('parts'),
                                      data=dict(
                                          name=name,
                                          model=model.id,
                                          parent=self.id,
                                          properties=json.dumps(properties_update_dict)
                                      ),
                                      params=dict(select_action=action))

            if r.status_code != requests.codes.created:
                raise APIError('{}: {}'.format(str(r), r.content))
            return Part(r.json()['results'][0], client=self._client)
        else:  # do the old way
            new_part = self.add(model, name=name)  # type: Part
            new_part.update(update_dict=update_dict, bulk=bulk)
            return new_part

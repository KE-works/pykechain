import json
from typing import Any, AnyStr  # flake8: noqa

import requests
from six import text_type

from pykechain.enums import Multiplicity, Category
from pykechain.exceptions import NotFoundError, APIError, MultipleFoundError, IllegalArgumentError
from pykechain.extra_utils import relocate_model, relocate_instance, move_part_instance
from pykechain.models.base import Base
from pykechain.models.property import Property
from pykechain.utils import find, is_uuid


class Part(Base):
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
        self.parent_id = json['parent'].get('id') if 'parent' in json and json.get('parent') else None
        self.properties = [Property.create(p, client=self._client) for p in json['properties']]
        self.multiplicity = json.get('multiplicity', None)
        self._cached_children = None

    def property(self, name):
        """Retrieve the property belonging to this part based on its name or uuid.

        :param name: property name or property UUID to search for
        :type name: basestring
        :return: a single :class:`Property`
        :raises NotFoundError: if the `Property` is not part of the `Part`

        Example
        -------

        >>> part = project.part('Bike')
        >>> part.properties
        [<pyke Property ...>, ...]
        # this returns a list of all properties of this part

        >>> gears = part.property('Gears')
        >>> gears.value
        6

        >>> gears = part.property('123e4567-e89b-12d3-a456-426655440000')
        >>> gears.value
        6

        """
        found = None
        if is_uuid(name):
            found = find(self.properties, lambda p: name == p.id)
        else:
            found = find(self.properties, lambda p: name == p.name)

        if not found:
            raise NotFoundError("Could not find property with name or id {}".format(name))

        return found

    def parent(self):
        # type: () -> Any
        """Retrieve the parent of this `Part`.

        :return: the parent :class:`Part` of this part
        :raises APIError: if an Error occurs

        Example
        -------

        >>> part = project.part('Frame')
        >>> bike = part.parent()

        """
        if self.parent_id:
            return self._client.part(pk=self.parent_id, category=self.category)
        else:
            return None

    def children(self, **kwargs):
        """Retrieve the children of this `Part` as `Partset`.

        When you call the :func:`Part.children()` method without any additional filtering options for the children,
        the children are cached to help speed up subsequent calls to retrieve the children. The cached children are
        returned as a list and not as a `Partset`.

        When you *do provide* additional keyword arguments (kwargs) that act as a specific children filter, the
        cached children are _not_ used and a separate API call is made to retrieve only those children.

        :param kwargs: Additional search arguments to search for, check :class:`pykechain.Client.parts`
                       for additional info
        :type kwargs: dict
        :return: a set of `Parts` as a :class:`PartSet`. Will be empty if no children. Will be a `List` if the
                 children are retrieved from the cached children.
        :raises APIError: When an error occurs.

        Example
        -------

        A normal call, which caches all children of the bike. If you call `bike.children` twice only 1 API call is made.

        >>> bike = project.part('Bike')
        >>> direct_descendants_of_bike = bike.children()

        An example with providing additional part search parameters 'name__icontains'. Children are retrieved from the
        API, not the bike's internal (already cached in previous example) cache.

        >>> bike = project.part('Bike')
        >>> wheel_children_of_bike = bike.children(name__icontains='wheel')

        """
        if not kwargs:
            # no kwargs provided is the default, we aim to cache it.
            if not self._cached_children:
                self._cached_children = list(self._client.parts(parent=self.id, category=self.category))
            return self._cached_children
        else:
            # if kwargs are provided, we assume no use of cache as specific filtering on the children is performed.
            return self._client.parts(parent=self.id, category=self.category, **kwargs)

    def siblings(self, **kwargs):
        # type: (Any) -> Any
        """Retrieve the siblings of this `Part` as `Partset`.

        Siblings are other Parts sharing the same parent of this `Part`, including the part itself.

        :param kwargs: Additional search arguments to search for, check :class:`pykechain.Client.parts`
                       for additional info
        :type kwargs: dict
        :return: a set of `Parts` as a :class:`PartSet`. Will be empty if no siblings.
        :raises APIError: When an error occurs.
        """
        if self.parent_id:
            return self._client.parts(parent=self.parent_id, category=self.category, **kwargs)
        else:
            from pykechain.models.partset import PartSet
            return PartSet(parts=[])

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
            model_id = self._json_data['model'].get('id')
            return self._client.model(pk=model_id)
        else:
            raise NotFoundError("Part {} has no model".format(self.name))

    def instances(self, **kwargs):
        """
        Retrieve the instances of this `Part` as a `PartSet`.

        For instance, if you have a model part, you can get the list of instances that are created based on this
        moodel. If there are no instances (only possible if the multiplicity is :attr:`enums.Multiplicity.ZERO_MANY`)
        than a :exc:`NotFoundError` is returned

        .. versionadded:: 1.8

        :return: the instances of this part model :class:`PartSet` with category `INSTANCE`
        :raises NotFoundError: if no instances found

        Example
        -------
        >>> wheel_model = project.model('Wheel')
        >>> wheel_instance_set = wheel_model.instances()

        An example with retrieving the front wheels only using the 'name__contains' search argument.

        >>> wheel_model = project.model('Wheel')
        >>> front_wheel_instances = wheel_model.instances(name__contains='Front')

        """
        if self.category == Category.MODEL:
            return self._client.parts(model=self, category=Category.INSTANCE, **kwargs)
        else:
            raise NotFoundError("Part {} is not a model".format(self.name))

    def instance(self):
        """
        Retrieve the single (expected) instance of this 'Part' (of `Category.MODEL`) as a 'Part'.

        See :func:`Part.instances()` method for documentation.

        :return: :class:`Part` with category `INSTANCE`
        :raises NotFoundError: if the instance does not exist
        :raises MultipleFoundError: if there are more than a single instance returned
        """
        instances_list = list(self.instances())
        if len(instances_list) == 1:
            return instances_list[0]
        elif len(instances_list) > 1:
            raise MultipleFoundError("Part {} has more than a single instance. "
                                     "Use the `Part.instances()` method".format(self.name))
        else:
            raise NotFoundError("Part {} has no instance".format(self.name))

    def proxy_model(self):
        """
        Retrieve the proxy model of this proxied `Part` as a `Part`.

        Allows you to retrieve the model of a proxy. But trying to get the catalog model of a part that
        has no proxy, will raise an :exc:`NotFoundError`. Only models can have a proxy.

        :return: :class:`Part` with category `MODEL` and from which the current part is proxied
        :raises NotFoundError: When no proxy model is found

        Example
        -------

        >>> proxy_part = project.model('Proxy based on catalog model')
        >>> catalog_model_of_proxy_part = proxy_part.proxy_model()

        >>> proxied_material_of_the_bolt_model = project.model('Bolt Material')
        >>> proxy_basis_for_the_material_model = proxied_material_of_the_bolt_model.proxy_model()

        """
        if self.category != Category.MODEL:
            raise IllegalArgumentError("Part {} is not a model, therefore it cannot have a proxy model".format(self))
        if 'proxy' in self._json_data and self._json_data.get('proxy'):
            catalog_model_id = self._json_data['proxy'].get('id')
            return self._client.model(pk=catalog_model_id)
        else:
            raise NotFoundError("Part {} is not a proxy".format(self.name))

    def add(self, model, **kwargs):
        # type: (Part, **Any) -> Part
        """Add a new child instance, based on a model, to this part.

        This can only act on instances. It needs a model from which to create the child instance.

        In order to prevent the backend from updating the frontend you may add `suppress_kevents=True` as
        additional keyword=value argument to this method. This will improve performance of the backend
        against a trade-off that someone looking at the frontend won't notice any changes unless the page
        is refreshed.

        :type kwargs: dict or None
        :type model: :class:`Part`
        :param kwargs: (optional) additional keyword=value arguments
        :type kwargs: dict
        :return: :class:`Part` with category `INSTANCE`.
        :raises APIError: if unable to add the new child instance

        Example
        -------

        >>> bike = project.part('Bike')
        >>> wheel_model = project.model('Wheel')
        >>> bike.add(wheel_model)
        """
        if self.category != Category.INSTANCE:
            raise APIError("Part should be of category INSTANCE")

        return self._client.create_part(self, model, **kwargs)

    def add_to(self, parent, **kwargs):
        # type: (Part, **Any) -> Part
        """Add a new instance of this model to a part.

        This works if the current part is a model and an instance of this model is to be added
        to a part instances in the tree.

        In order to prevent the backend from updating the frontend you may add `suppress_kevents=True` as
        additional keyword=value argument to this method. This will improve performance of the backend
        against a trade-off that someone looking at the frontend won't notice any changes unless the page
        is refreshed.

        :param parent: part to add the new instance to
        :param kwargs: (optional) additional kwargs that will be passed in the during the edit/update request
        :type kwargs: dict or None
        :type parent: :class:`Part`
        :param kwargs: (optional) additional keyword=value arguments
        :type kwargs: dict
        :return: :class:`Part` with category `INSTANCE`
        :raises APIError: if unable to add the new child instance

        Example
        -------

        >>> wheel_model = project.model('wheel')
        >>> bike = project.part('Bike')
        >>> wheel_model.add_to(bike)
        """
        if self.category != Category.MODEL:
            raise APIError("Part should be of category MODEL")

        return self._client.create_part(parent, self, **kwargs)

    def add_model(self, *args, **kwargs):
        # type: (*Any, **Any) -> Part
        """Add a new child model to this model.

        In order to prevent the backend from updating the frontend you may add `suppress_kevents=True` as
        additional keyword=value argument to this method. This will improve performance of the backend
        against a trade-off that someone looking at the frontend won't notice any changes unless the page
        is refreshed.

        :return: a :class:`Part` of category `MODEL`
        """
        if self.category != Category.MODEL:
            raise APIError("Part should be of category MODEL")

        return self._client.create_model(self, *args, **kwargs)

    def add_proxy_to(self, parent, name, multiplicity=Multiplicity.ONE_MANY, **kwargs):
        # type: (Any, AnyStr, Any, **Any) -> Part
        """Add this model as a proxy to another parent model.

        This will add the current model as a proxy model to another parent model. It ensure that it will copy the
        whole subassembly to the 'parent' model.

        In order to prevent the backend from updating the frontend you may add `suppress_kevents=True` as
        additional keyword=value argument to this method. This will improve performance of the backend
        against a trade-off that someone looking at the frontend won't notice any changes unless the page
        is refreshed.

        :param name: Name of the new proxy model
        :type name: basestring
        :param parent: parent of the to be proxied model
        :type parent: :class:`Part`
        :param multiplicity: the multiplicity of the new proxy model (default ONE_MANY)
        :type multiplicity: basestring or None
        :param kwargs: (optional) additional kwargs that will be passed in the during the edit/update request
        :type kwargs: dict or None
        :return: the new proxied :class:`Part`.
        :raises APIError: in case an Error occurs

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
        return self._client.create_proxy_model(self, parent, name, multiplicity, **kwargs)

    def add_property(self, *args, **kwargs):
        # type: (*Any, **Any) -> Property
        """Add a new property to this model.

        See :class:`pykechain.Client.create_property` for available parameters.

        :return: :class:`Property`
        :raises APIError: in case an Error occurs
        """
        if self.category != Category.MODEL:
            raise APIError("Part should be of category MODEL")

        return self._client.create_property(self, *args, **kwargs)

    def delete(self):
        # type: () -> None
        """Delete this part.

        :return: None
        :raises APIError: in case an Error occurs
        """
        r = self._client._request('DELETE', self._client._build_url('part', part_id=self.id))

        if r.status_code != requests.codes.no_content:  # pragma: no cover
            raise APIError("Could not delete part: {} with id {}".format(self.name, self.id))

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
        r = self._client._request('PUT', self._client._build_url('part', part_id=self.id), json=update_dict)

        if r.status_code != requests.codes.ok:  # pragma: no cover
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
            style = "color:blue;" if prop._json_data.get('output', False) else ""

            html.append("<tr style=\"{}\">".format(style))
            html.append("<td>{}</td>".format(prop.name))
            html.append("<td>{}</td>".format(prop.value))
            html.append("</tr>")

        html.append("</table>")

        return ''.join(html)

    def update(self, name=None, update_dict=None, bulk=True, **kwargs):
        """
        Edit part name and property values in one go.

        In order to prevent the backend from updating the frontend you may add `suppress_kevents=True` as
        additional keyword=value argument to this method. This will improve performance of the backend
        against a trade-off that someone looking at the frontend won't notice any changes unless the page
        is refreshed.

        :param name: new part name (defined as a string)
        :type name: basestring or None
        :param update_dict: dictionary with keys being property names (str) or property ids (uuid)
                            and values being property values
        :type update_dict: dict
        :param bulk: True to use the bulk_update_properties API endpoint for KE-chain versions later then 2.1.0b
        :type bulk: boolean or None
        :param kwargs: (optional) additional keyword arguments that will be passed inside the update request
        :type kwargs: dict or None
        :return: the updated :class:`Part`
        :raises NotFoundError: when the property name is not a valid property of this part
        :raises IllegalArgumentError: when the type or value of an argument provided is incorrect
        :raises APIError: in case an Error occurs

        Example
        -------

        >>> bike = client.scope('Bike Project').part('Bike')
        >>> bike.update(name='Good name', update_dict={'Gears': 11, 'Total Height': 56.3}, bulk=True)

        """
        # dict(name=name, properties=json.dumps(update_dict))) with property ids:value
        action = 'bulk_update_properties'

        url = self._client._build_url('part', part_id=self.id)

        request_body = dict()
        for prop_name_or_id, property_value in update_dict.items():
            if is_uuid(prop_name_or_id):
                request_body[prop_name_or_id] = property_value
            else:
                request_body[self.property(prop_name_or_id).id] = property_value

        if bulk and len(update_dict.keys()) > 1:
            if name:
                if not isinstance(name, str):
                    raise IllegalArgumentError("Name of the part should be provided as a string")
            r = self._client._request('PUT', self._client._build_url('part', part_id=self.id),
                                      data=dict(name=name, properties=json.dumps(request_body), **kwargs),
                                      params=dict(select_action=action))
            if r.status_code != requests.codes.ok:  # pragma: no cover
                raise APIError('{}: {}'.format(str(r), r.content))
        else:
            for property_name, property_value in update_dict.items():
                self.property(property_name).value = property_value

    def add_with_properties(self, model, name=None, update_dict=None, bulk=True, **kwargs):
        """
        Add a part and update its properties in one go.

        In order to prevent the backend from updating the frontend you may add `suppress_kevents=True` as
        additional keyword=value argument to this method. This will improve performance of the backend
        against a trade-off that someone looking at the frontend won't notice any changes unless the page
        is refreshed.

        :param model: model of the part which to add a new instance, should follow the model tree in KE-chain
        :type model: :class:`Part`
        :param name: (optional) name provided for the new instance as string otherwise use the name of the model
        :type name: basestring or None
        :param update_dict: dictionary with keys being property names (str) or property_id (from the property models)
                            and values being property values
        :type update_dict: dict or None
        :param bulk: True to use the bulk_update_properties API endpoint for KE-chain versions later then 2.1.0b
        :type bulk: boolean or None
        :param kwargs: (optional) additional keyword arguments that will be passed inside the update request
        :type kwargs: dict or None
        :return: the newly created :class:`Part`
        :raises NotFoundError: when the property name is not a valid property of this part
        :raises APIError: in case an Error occurs

        Examples
        --------
        >>> bike = client.scope('Bike Project').part('Bike')
        >>> wheel_model = client.scope('Bike Project').model('Wheel')
        >>> bike.add_with_properties(wheel_model, 'Wooden Wheel', {'Spokes': 11, 'Material': 'Wood'})

        """
        if self.category != Category.INSTANCE:
            raise APIError("Part should be of category INSTANCE")
        name = name or model.name
        action = 'new_instance_with_properties'

        properties_update_dict = dict()
        for prop_name_or_id, property_value in update_dict.items():
            if is_uuid(prop_name_or_id):
                properties_update_dict[prop_name_or_id] = property_value
            else:
                properties_update_dict[model.property(prop_name_or_id).id] = property_value

        if bulk:
            r = self._client._request('POST', self._client._build_url('parts'),
                                      data=dict(
                                          name=name,
                                          model=model.id,
                                          parent=self.id,
                                          properties=json.dumps(properties_update_dict),
                                          **kwargs
                                      ),
                                      params=dict(select_action=action))

            if r.status_code != requests.codes.created:  # pragma: no cover
                raise APIError('{}: {}'.format(str(r), r.content))
            return Part(r.json()['results'][0], client=self._client)
        else:  # do the old way
            new_part = self.add(model, name=name)  # type: Part
            new_part.update(update_dict=update_dict, bulk=bulk)
            return new_part

    def as_dict(self):
        """
        Retrieve the properties of a part inside a dict in this structure: {property_name: property_value}.

        .. versionadded:: 1.9

        :returns: the values of the properties as a `dict`
        :rtype: dict

        Example
        -------
        >>> front_wheel = client.scope('Bike Project').part('Front Wheel')
        >>> front_wheel_properties = front_wheel.as_dict()
        {'Diameter': 60.8,
         'Spokes': 24,
         'Rim Material': 'Aluminium',
         'Tire Thickness': 4.2}

        """
        properties_dict = dict()
        for prop in self.properties:
            properties_dict[prop.name] = prop.value
        return properties_dict

    def order_properties(self, property_list=None):
        """
        Order the properties of a part model using a list of property objects or property names or property id's.

        :param property_list: ordered list of property names (basestring) or property id's (uuid)
        :type property_list: list(basestring)
        :returns: the :class:`Part` with the reordered list of properties
        :raises APIError: when an Error occurs
        :raises IllegalArgumentError: When provided a wrong argument

        Examples
        --------
        >>> front_fork = client.scope('Bike Project').model('Front Fork')
        >>> front_fork.order_properties(['Material', 'Height (mm)', 'Color'])

        >>> front_fork = client.scope('Bike Project').model('Front Fork')
        >>> material = front_fork.property('Material')
        >>> height = front_fork.property('Height (mm)')
        >>> color = front_fork.property('Color')
        >>> front_fork.order_properties([material, height, color])

        """
        if self.category != Category.MODEL:
            raise APIError("Part should be of category MODEL")
        if not isinstance(property_list, list):
            raise IllegalArgumentError('Expected a list of strings or Property() objects, got a {} object'.
                                       format(type(property_list)))

        order_dict = dict()

        for prop in property_list:
            if isinstance(prop, (str, text_type)):
                order_dict[self.property(name=prop).id] = property_list.index(prop)
            else:
                order_dict[prop.id] = property_list.index(prop)

        r = self._client._request('PUT', self._client._build_url('part', part_id=self.id),
                                  data=dict(
                                      property_order=json.dumps(order_dict)
                                  ))
        if r.status_code != requests.codes.ok:  # pragma: no cover
            raise APIError("Could not reorder properties")

    def populate_descendants(self, batch=200):
        """
        Retrieve the descendants of a specific part in a list of dicts and populate the :func:`Part.children()` method.

        Each `Part` has a :func:`Part.children()` method to retrieve the children on the go. This function
        prepopulates the children and the children's children with its children in one call, making the traversal
        through the parttree blazingly fast.

        .. versionadded:: 2.1

        :param batch: Number of Parts to be retrieved in a batch
        :type batch: int (defaults to 200)
        :returns: list of `Parts` with `children`
        :raises APIError: if you cannot create the children tree.

        Example
        -------
        >>> bike = client.part('Bike')
        >>> bike.populate_descendants(batch=150)

        """
        descendants_flat_list = list(self._client.parts(pk=self.id, category=self.category, descendants='children',
                                                        batch=batch))

        for parent in descendants_flat_list:
            parent._cached_children = list()
            for child in descendants_flat_list:
                if child.parent_id == parent.id:
                    parent._cached_children.append(child)

        self._cached_children = descendants_flat_list[0]._cached_children

    def clone(self, **kwargs):
        """
        Clone a part.

        .. versionadded:: 2.3

        :param kwargs: (optional) additional keyword=value arguments
        :type kwargs: dict
        :return: cloned :class:`models.Part`
        :raises APIError: if the `Part` could not be cloned

        Example
        -------
        >>> bike = client.model('Bike')
        >>> bike2 = bike.clone()

        """
        parent = self.parent()
        return self._client._create_clone(parent, self, **kwargs)

    def copy(self, target_parent, name=None, include_children=True, include_instances=True):
        """
        Copy the `Part` to target parent, both of them having the same category.

        .. versionadded:: 2.3

        :param target_parent: `Part` object under which the desired `Part` is copied
        :type target_parent: :class:`Part`
        :param name: how the copied top-level `Part` should be called
        :type name: basestring
        :param include_children: True to copy also the descendants of `Part`.
        :type include_children: bool
        :param include_instances: True to copy also the instances of `Part` to ALL the instances of target_parent.
        :type include_instances: bool
        :returns: copied :class:`Part` model.
        :raises IllegalArgumentError: if part and target_parent have different `Category`
        :raises IllegalArgumentError: if part and target_parent are identical

        Example
        -------
        >>> model_to_copy = client.model(name='Model to be copied')
        >>> bike = client.model('Bike')
        >>> model_to_copy.copy(target_parent=bike, name='Copied model',
        >>>                    include_children=True,
        >>>                    include_instances=True)

        """
        if self.category == Category.MODEL and target_parent.category == Category.MODEL:
            # Cannot add a model under an instance or vice versa
            copied_model = relocate_model(part=self, target_parent=target_parent, name=name,
                                          include_children=include_children)
            if include_instances:
                instances_to_be_copied = list(self.instances())
                parent_instances = list(target_parent.instances())
                for parent_instance in parent_instances:
                    for instance in instances_to_be_copied:
                        instance.populate_descendants()
                        move_part_instance(part_instance=instance, target_parent=parent_instance,
                                           part_model=self, name=instance.name, include_children=include_children)
            return copied_model

        elif self.category == Category.INSTANCE and target_parent.category == Category.INSTANCE:
            copied_instance = relocate_instance(part=self, target_parent=target_parent, name=name,
                                                include_children=include_children)
            return copied_instance
        else:
            raise IllegalArgumentError('part "{}" and target parent "{}" must have the same category')

    def move(self, target_parent, name=None, include_children=True, include_instances=True):
        """
        Move the `Part` to target parent, both of them the same category.

        .. versionadded:: 2.3

        :param target_parent: `Part` object under which the desired `Part` is moved
        :type target_parent: :class:`Part`
        :param name: how the moved top-level `Part` should be called
        :type name: basestring
        :param include_children: True to move also the descendants of `Part`. If False, the children will be lost.
        :type include_children: bool
        :param include_instances: True to move also the instances of `Part` to ALL the instances of target_parent.
        :type include_instances: bool
        :returns: moved :class:`Part` model.
        :raises IllegalArgumentError: if part and target_parent have different `Category`
        :raises IllegalArgumentError: if target_parent is descendant of part

        Example
        -------
        >>> model_to_move = client.model(name='Model to be moved')
        >>> bike = client.model('Bike')
        >>> model_to_move.move(target_parent=bike, name='Moved model',
        >>>                    include_children=True,
        >>>                    include_instances=True)

        """
        if not name:
            name = self.name
        if self.category == Category.MODEL and target_parent.category == Category.MODEL:
            moved_model = relocate_model(part=self, target_parent=target_parent, name=name,
                                         include_children=include_children)
            if include_instances:
                retrieve_instances_to_copied = list(self.instances())
                retrieve_parent_instances = list(target_parent.instances())
                for parent_instance in retrieve_parent_instances:
                    for instance in retrieve_instances_to_copied:
                        instance.populate_descendants()
                        move_part_instance(part_instance=instance, target_parent=parent_instance,
                                           part_model=self, name=instance.name, include_children=include_children)
            self.delete()
            return moved_model
        elif self.category == Category.INSTANCE and target_parent.category == Category.INSTANCE:
            moved_instance = relocate_instance(part=self, target_parent=target_parent, name=name,
                                               include_children=include_children)
            try:
                self.delete()
            except APIError:
                model_of_instance = self.model()
                model_of_instance.delete()
            return moved_instance
        else:
            raise IllegalArgumentError('part "{}" and target parent "{}" must have the same category')

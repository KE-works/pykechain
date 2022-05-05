from typing import Union, List, Dict, Optional, Tuple, Any  # noqa: F401

import requests

from pykechain.defaults import API_EXTRA_PARAMS, PARTS_BATCH_LIMIT
from pykechain.enums import Category, Multiplicity, Classification, PropertyType
from pykechain.exceptions import (
    APIError,
    IllegalArgumentError,
    NotFoundError,
    MultipleFoundError,
)
from pykechain.models.input_checks import (
    check_text,
    check_type,
    check_list_of_base,
    check_list_of_dicts,
)
from pykechain.models.property import Property
from pykechain.models.tree_traversal import TreeObject
from pykechain.utils import find_obj_in_list, find, Empty, clean_empty_values, empty


class Part(TreeObject):
    """A virtual object representing a KE-chain part.

    :ivar id: UUID of the part
    :type id: basestring
    :ivar name: Name of the part
    :type name: basestring
    :ivar ref: Reference of the part (slug of the original name)
    :type ref: basestring
    :ivar description: description of the part
    :type description: basestring or None
    :ivar created_at: the datetime when the object was created if available (otherwise None)
    :type created_at: datetime or None
    :ivar updated_at: the datetime when the object was last updated if available (otherwise None)
    :type updated_at: datetime or None
    :ivar category: The category of the part, either 'MODEL' or 'INSTANCE' (of :class:`pykechain.enums.Category`)
    :type category: basestring
    :ivar parent_id: The UUID of the parent of this part
    :type parent_id: basestring or None
    :ivar properties: The list of :class:`Property` objects belonging to this part.
    :type properties: List[Property]
    :ivar multiplicity: The multiplicity of the part being one of the following options: ZERO_ONE, ONE, ZERO_MANY,
                        ONE_MANY, (reserved) M_N (of :class:`pykechain.enums.Multiplicity`)
    :type multiplicity: basestring
    :ivar scope_id: scope UUID of the Part
    :type scope_id: basestring
    :ivar properties: the list of properties of this part
    :type properties: List[AnyProperty]

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

    def __init__(self, json: Dict, **kwargs):
        """Construct a part from a KE-chain 2 json response.

        :param json: the json response to construct the :class:`Part` from
        :type json: dict
        """
        # we need to run the init of 'Base' instead of 'Part' as we do not need the instantiation of properties
        super().__init__(json, **kwargs)

        self.ref: str = json.get("ref")
        self.model_id: str = json.get("model_id")
        self.category: Category = json.get("category")
        self.description: str = json.get("description")
        self.multiplicity: str = json.get("multiplicity")
        self.classification: Classification = json.get("classification")

        sorted_properties: List[Dict] = sorted(
            json["properties"], key=lambda p: p.get("order", 0)
        )
        self.properties: List[Property] = [
            Property.create(p, client=self._client) for p in sorted_properties
        ]

        proxy_data: Optional[Dict] = json.get("proxy_source_id_name", dict())
        self._proxy_model_id: Optional[str] = (
            proxy_data.get("id") if proxy_data else None
        )

    def __call__(self, *args, **kwargs) -> "Part":
        """Short-hand version of the `child` method."""
        return self.child(*args, **kwargs)

    def refresh(
        self,
        json: Optional[Dict] = None,
        url: Optional[str] = None,
        extra_params: Optional[Dict] = None,
    ):
        """Refresh the object in place."""
        if extra_params is None:
            extra_params = {}
        extra_params.update(API_EXTRA_PARAMS["part"])
        existing_properties = {p.id: p for p in self.properties}

        super().refresh(
            json=json,
            url=self._client._build_url("part", part_id=self.id),
            extra_params=extra_params,
        )

        # The properties have been recreated anew when refreshing the part, but should be refreshed in-place.
        new_properties = list(self.properties)
        self.properties = []
        for new_prop in new_properties:
            if new_prop.id in existing_properties:
                prop = existing_properties.pop(new_prop.id)
                prop.refresh(json=new_prop._json_data)
            else:
                prop = new_prop
            self.properties.append(prop)

    #
    # Family and structure methods
    #

    def property(self, name: str = None) -> "AnyProperty":
        """Retrieve the property belonging to this part based on its name, ref or uuid.

        :param name: property name, ref or UUID to search for
        :return: a single :class:`Property`
        :raises NotFoundError: if the `Property` is not part of the `Part`
        :raises MultipleFoundError

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
        return find_obj_in_list(name, iterable=self.properties)

    def scope(self) -> "Scope":
        """Scope this Part belongs to.

        This property will return a `Scope` object. It will make an additional call to the KE-chain API.

        :return: the scope
        :rtype: :class:`pykechain.models.Scope`
        :raises NotFoundError: if the scope could not be found
        """
        return super().scope

    def parent(self) -> "Part":
        """Retrieve the parent of this `Part`.

        :return: the parent :class:`Part` of this part
        :raises APIError: if an Error occurs

        Example
        -------
        >>> part = project.part('Frame')
        >>> bike = part.parent()

        """
        if self._parent is None and self.parent_id:
            self._parent = self._client.part(pk=self.parent_id, category=self.category)
        return self._parent

    def children(self, **kwargs) -> Union["PartSet", List["Part"]]:
        """Retrieve the children of this `Part` as `PartSet`.

        When you call the :func:`Part.children()` method without any additional filtering options for the children,
        the children are cached to help speed up subsequent calls to retrieve the children. The cached children are
        returned as a list and not as a `Partset`.

        When you *do provide* additional keyword arguments (kwargs) that act as a specific children filter, the
        cached children are _not_ used and a separate API call is made to retrieve only those children.

        :param kwargs: Additional search arguments to search for, check :class:`pykechain.Client.parts`
                       for additional info
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
            if self._cached_children is None:
                self._cached_children = list(
                    self._client.parts(parent=self.id, category=self.category)
                )
                for child in self._cached_children:
                    child._parent = self
            return self._cached_children
        else:
            # if kwargs are provided, we assume no use of cache as specific filtering on the children is performed.
            return self._client.parts(parent=self.id, category=self.category, **kwargs)

    def child(
        self, name: Optional[str] = None, pk: Optional[str] = None, **kwargs
    ) -> "Part":
        """
        Retrieve a child object.

        :param name: optional, name of the child
        :type name: str
        :param pk: optional, UUID of the child
        :type: pk: str
        :return: Child object
        :raises MultipleFoundError: whenever multiple children fit match inputs.
        :raises NotFoundError: whenever no child matching the inputs could be found.
        """
        if not (name or pk):
            raise IllegalArgumentError('You need to provide either "name" or "pk".')

        if self._cached_children:
            # First try to find the child without calling KE-chain.
            if name:
                part_list = [c for c in self.children() if c.name == name]
            else:
                part_list = [c for c in self.children() if c.id == pk]
        else:
            part_list = []

        if not part_list:
            # Refresh children list from KE-chain by using a keyword-argument.
            if name:
                part_list = self.children(name=name)
            else:
                part_list = self.children(pk=pk)

        criteria = f"\nname: {name}\npk: {pk}\nkwargs: {kwargs}"

        # If there is only one, then that is the part you are looking for
        if len(part_list) == 1:
            part = part_list[0]

        # Otherwise raise the appropriate error
        elif len(part_list) > 1:
            raise MultipleFoundError(
                f"{self} has more than one matching child.{criteria}"
            )
        else:
            raise NotFoundError(f"{self} has no matching child.{criteria}")
        return part

    def populate_descendants(self, batch: int = PARTS_BATCH_LIMIT) -> None:
        """
        Retrieve the descendants of a specific part in a list of dicts and populate the :func:`Part.children()` method.

        Each `Part` has a :func:`Part.children()` method to retrieve the children on the go. This function
        prepopulates the children and the children's children with its children in one call, making the traversal
        through the parttree blazingly fast.

        .. versionadded:: 2.1

        .. versionchanged:: 3.3.2 now populates child parts instead of this part

        :param batch: Number of Parts to be retrieved in a batch
        :type batch: int (defaults to 100)
        :returns: None
        :raises APIError: if you cannot create the children tree.

        Example
        -------
        >>> bike = project.part('Bike')
        >>> bike.populate_descendants(batch=150)

        """
        all_descendants = list(
            self._client.parts(
                category=self.category,
                batch=batch,
                descendants=self.id,
            )
        )[
            1:
        ]  # remove the part itself, which is returned on index 0

        self._populate_cached_children(all_descendants=all_descendants, overwrite=True)

        return None

    def all_children(self) -> List["Part"]:
        """
        Retrieve a flat list of all descendants, sorted depth-first. Also populates all descendants.

        :returns list of child objects
        :rtype List
        """
        if self._cached_children is None:
            self.populate_descendants()
        return super().all_children()

    def siblings(self, **kwargs) -> Union["PartSet", List["Part"]]:
        """Retrieve the siblings of this `Part` as `PartSet`.

        Siblings are other Parts sharing the same parent of this `Part`, including the part itself.

        :param kwargs: Additional search arguments to search for, check :class:`pykechain.Client.parts`
                       for additional info
        :return: a set of `Parts` as a :class:`PartSet`. Will be empty if no siblings.
        :raises APIError: When an error occurs.
        """
        if self.parent_id:
            return self._client.parts(
                parent=self.parent_id, category=self.category, **kwargs
            )
        else:
            from pykechain.models.partset import PartSet

            return PartSet(parts=[])

    #
    # Model and Instance(s) methods
    #

    def model(self) -> "Part":
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
            return self._client.model(pk=self.model_id)
        else:
            raise NotFoundError(f'Part "{self}" already is a model')

    def instances(self, **kwargs) -> Union["PartSet", List["Part"]]:
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
            raise NotFoundError(
                f"Part '{self}' is not a model, hence it has no instances."
            )

    def instance(self) -> "Part":
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
            raise MultipleFoundError(
                "Part {} has more than a single instance. "
                "Use the `Part.instances()` method".format(self)
            )
        else:
            raise NotFoundError(f"Part {self} has no instance")

    def count_instances(self) -> int:
        """
        Retrieve the number of instances of this Part model without the parts themselves.

        :return: number of Part instances
        :rtype
        """
        if not self.category == Category.MODEL:
            raise IllegalArgumentError(
                "You can only count the number of instances of a Part with category MODEL"
            )

        response = self._client._request(
            "GET",
            self._client._build_url("parts"),
            params={
                "scope_id": self.scope_id,
                "model_id": self.id,
                "limit": 1,
            },
        )

        if response.status_code != requests.codes.ok:  # pragma: no cover
            raise NotFoundError("Could not retrieve Parts instances")

        count = response.json()["count"]

        return count

    def count_children(self, **kwargs) -> int:
        """
        Retrieve the number of child parts using a light-weight request.

        :return: number of Parts
        :rtype int
        """
        return super().count_children(method="parts", category=self.category, **kwargs)

    #
    # CRUD operations
    #

    def edit(
        self,
        name: Optional[Union[str, Empty]] = empty,
        description: Optional[Union[str, Empty]] = empty,
        **kwargs,
    ) -> None:
        """Edit the details of a part (model or instance).

        Setting an input to None will clear out the value (exception being name).

        For an instance you can edit the Part instance name and the part instance description. To alter the values
        of properties use :func:`Part.update()`.

        In order to prevent the backend from updating the frontend you may add `suppress_kevents=True` as
        additional keyword=value argument to this method. This will improve performance of the backend
        against a trade-off that someone looking at the frontend won't notice any changes unless the page
        is refreshed.

        :param name: optional name of the part to edit. Cannot be cleared.
        :type name: basestring or None or Empty
        :param description: (optional) description of the part. Can be cleared.
        :type description: basestring or None or Empty
        :param kwargs: (optional) additional kwargs that will be passed in the during the edit/update request
        :return: None
        :raises IllegalArgumentError: when the type or value of an argument provided is incorrect
        :raises APIError: in case an Error occurs

        Example
        -------
        For changing a part:

        >>> front_fork = project.part('Front Fork')
        >>> front_fork.edit(name='Front Fork - updated')
        >>> front_fork.edit(name='Front Fork cruizer',description='With my ragtop down so my hair can blow')

        for changing a model:

        >>> front_fork = project.model('Front Fork')
        >>> front_fork.edit(name='Front Fork basemodel',description='Some description here')

        Not mentioning an input parameter in the function will leave it unchanged. Setting a parameter as None will
        clear its value (where that is possible). The example below will clear the description and edit the name.

        >>> front_fork.edit(name="Front spoon",description=None)

        """
        update_dict = {
            "id": self.id,
            "name": check_text(name, "name") or self.name,
            "description": check_text(description, "description") or "",
        }

        if kwargs:  # pragma: no cover
            update_dict.update(**kwargs)

        update_dict = clean_empty_values(update_dict=update_dict)

        response = self._client._request(
            "PUT",
            self._client._build_url("part", part_id=self.id),
            params=API_EXTRA_PARAMS["part"],
            json=update_dict,
        )

        if response.status_code != requests.codes.ok:  # pragma: no cover
            raise APIError(f"Could not update Part {self}", response=response)

        self.refresh(json=response.json().get("results")[0])

    def proxy_model(self) -> "Part":
        """
        Retrieve the proxy model of this proxied `Part` as a `Part`.

        Allows you to retrieve the model of a proxy. But trying to get the catalog model of a part that
        has no proxy, will raise an :exc:`NotFoundError`. Only models can have a proxy.

        .. versionchanged:: 3.0
           Added compatibility with KE-chain 3 backend.

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
            raise IllegalArgumentError(
                f'Part "{self}" is not a product model, therefore it cannot have a proxy model'
            )
        if self.classification != Classification.PRODUCT or not self._proxy_model_id:
            raise NotFoundError(
                f'Part "{self}" is not a product model, therefore it cannot have a proxy model'
            )

        return self._client.model(pk=self._proxy_model_id)

    def add(self, model: "Part", **kwargs) -> "Part":
        """Add a new child instance, based on a model, to this part.

        This can only act on instances. It needs a model from which to create the child instance.

        In order to prevent the backend from updating the frontend you may add `suppress_kevents=True` as
        additional keyword=value argument to this method. This will improve performance of the backend
        against a trade-off that someone looking at the frontend won't notice any changes unless the page
        is refreshed.

        :param model: `Part` object with category `MODEL`.
        :type model: :class:`Part`
        :param kwargs: (optional) additional keyword=value arguments
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

        new_instance = self._client.create_part(self, model, **kwargs)

        if self._cached_children is not None:
            self._cached_children.append(new_instance)

        return new_instance

    def add_to(self, parent: "Part", **kwargs) -> "Part":
        """Add a new instance of this model to a part.

        This works if the current part is a model and an instance of this model is to be added
        to a part instances in the tree.

        In order to prevent the backend from updating the frontend you may add `suppress_kevents=True` as
        additional keyword=value argument to this method. This will improve performance of the backend
        against a trade-off that someone looking at the frontend won't notice any changes unless the page
        is refreshed.

        :param parent: part to add the new instance to
        :type parent: :class:`Part`
        :param kwargs: (optional) additional kwargs that will be passed in the during the edit/update request
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

        new_instance = self._client.create_part(parent, self, **kwargs)

        if parent._cached_children is not None:
            parent._cached_children.append(new_instance)

        return new_instance

    def add_model(self, *args, **kwargs) -> "Part":
        """Add a new child model to this model.

        In order to prevent the backend from updating the frontend you may add `suppress_kevents=True` as
        additional keyword=value argument to this method. This will improve performance of the backend
        against a trade-off that someone looking at the frontend won't notice any changes unless the page
        is refreshed.

        :return: a :class:`Part` of category `MODEL`
        """
        if self.category != Category.MODEL:
            raise APIError("Part should be of category MODEL")

        new_model = self._client.create_model(self, *args, **kwargs)

        if self._cached_children is not None:
            self._cached_children.append(new_model)

        return new_model

    def add_proxy_to(
        self,
        parent: "Part",
        name: str,
        multiplicity: Multiplicity = Multiplicity.ONE_MANY,
        **kwargs,
    ) -> "Part":
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
        return self._client.create_proxy_model(
            self, parent, name, multiplicity, **kwargs
        )

    def add_property(self, *args, **kwargs) -> "AnyProperty":
        """Add a new property to this model.

        See :class:`pykechain.Client.create_property` for available parameters.

        :return: :class:`Property`
        :raises APIError: in case an Error occurs
        """
        if self.category != Category.MODEL:
            raise APIError("Part should be of category MODEL")

        return self._client.create_property(self, *args, **kwargs)

    @staticmethod
    def _parse_update_dict(
        part: "Part",
        properties_fvalues: List[Dict[str, Any]],
        update_dict: Dict,
        creating: bool = False,
    ) -> Tuple[List[Dict], List[Dict], Dict]:
        """
        Check the content of the update dict and insert them into the properties_fvalues list.

        :param part: Depending on whether you add to or update a part, this is the model or the part itself, resp.
        :param properties_fvalues: list of property values
        :param update_dict: dictionary with property values, keyed by property names
        :param creating: flag to indicate creation of new properties, hence using the `model_id` instead of `id`
        :return: Tuple with 2 lists of dicts
        :rtype tuple
        """
        properties_fvalues = (
            check_list_of_dicts(properties_fvalues, "properties_fvalues") or list()
        )
        check_type(update_dict, dict, "update_dict")

        exception_fvalues = list()
        update_dict = update_dict or dict()

        key = "model_id" if creating else "id"

        parsed_dict = dict()

        for prop_name_or_id, property_value in update_dict.items():
            property_to_update: Property = part.property(prop_name_or_id)

            updated_p = {
                "value": property_to_update.serialize_value(property_value),
                key: property_to_update.id,
            }
            parsed_dict[property_to_update.id] = property_value

            if property_to_update.type == PropertyType.ATTACHMENT_VALUE:
                exception_fvalues.append(updated_p)
            else:
                properties_fvalues.append(updated_p)

        return properties_fvalues, exception_fvalues, parsed_dict

    def add_with_properties(
        self,
        model: "Part",
        name: Optional[str] = None,
        update_dict: Optional[Dict] = None,
        properties_fvalues: Optional[List[Dict]] = None,
        **kwargs,
    ) -> "Part":
        """
        Add a new part instance of a model as a child of this part instance and update its properties in one go.

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

        .. versionchanged:: 3.3
           The 'refresh' flag is pending deprecation in version 3.4.. This flag had an effect of refreshing
           the list of children of the current part and was default set to True. This resulted in large
           processing times int he API as every `add_with_properties()` the children of the parent where all
           retrieved. The default is now 'False'. The part just created is however to the internal list of children
           once these children are retrieved earlier.

        :param model: model of the part which to add a new instance, should follow the model tree in KE-chain
        :type model: :class:`Part`
        :param name: (optional) name provided for the new instance as string otherwise use the name of the model
        :type name: basestring or None
        :param update_dict: dictionary with keys being property names (str) or property_id (from the property models)
                            and values being property values
        :type update_dict: dict or None
        :param properties_fvalues: (optional) keyword argument with raw list of properties update dicts
        :type properties_fvalues: list of dict or None
        :param kwargs: (optional) additional keyword arguments that will be passed inside the update request
        :return: the newly created :class:`Part`
        :raises NotFoundError: when the property name is not a valid property of this part
        :raises APIError: in case an Error occurs
        :raises IllegalArgumentError: in case of illegal arguments.

        Examples
        --------
        >>> bike = project.part('Bike')
        >>> wheel_model = project.model('Wheel')
        >>> bike.add_with_properties(wheel_model, 'Wooden Wheel', {'Spokes': 11, 'Material': 'Wood'})

        """
        if self.category != Category.INSTANCE:
            raise APIError("Part should be of category INSTANCE")

        if not isinstance(model, Part) or model.category != Category.MODEL:
            raise IllegalArgumentError(
                f'`model` must be a Part object of category MODEL, "{model}" is not.'
            )

        instance_name = check_text(name, "name") or model.name
        properties_fvalues, exception_fvalues, _ = self._parse_update_dict(
            model,
            properties_fvalues,
            update_dict,
            creating=True,
        )

        url = self._client._build_url("parts_new_instance")
        response = self._client._request(
            "POST",
            url,
            params=API_EXTRA_PARAMS["parts"],
            json=dict(
                name=instance_name,
                model_id=model.id,
                parent_id=self.id,
                properties_fvalues=properties_fvalues,
                **kwargs,
            ),
        )

        if response.status_code != requests.codes.created:  # pragma: no cover
            raise APIError(f"Could not add to Part {self}", response=response)

        new_part_instance: Part = Part(
            response.json()["results"][0], client=self._client
        )

        # ensure that cached children are updated
        if self._cached_children is not None:
            self._cached_children.append(new_part_instance)

        # If any values were not set via the json, set them individually
        for exception_fvalue in exception_fvalues:
            property_model_id = exception_fvalue["model_id"]
            property_instance = find(
                new_part_instance.properties, lambda p: p.model_id == property_model_id
            )
            property_instance.value = exception_fvalue["value"]

        return new_part_instance

    def clone(self, **kwargs) -> "Part":
        """
        Clone a part.

        An optional name of the cloned part may be provided. If not provided the name will be set
        to "CLONE - <part name>". (available for KE-chain 3 backends only)
        An optional multiplicity, may be added as paremeter for the cloning of models. If not
        provided the multiplicity of the part will be used. (available for KE-chain 3 backends only)

        .. versionadded:: 2.3
        .. versionchanged:: 3.0
           Added optional paramenters the name and multiplicity for KE-chain 3 backends.

        :param kwargs: (optional) additional keyword=value arguments
        :return: cloned :class:`models.Part`
        :raises APIError: if the `Part` could not be cloned

        Example
        -------
        >>> bike = project.model('Bike')
        >>> bike2 = bike.clone()

        For KE-chain 3 backends

        >>> bike = project.model('Bike')
        >>> bike2 = bike.clone(name='Trike', multiplicity=Multiplicity.ZERO_MANY)

        """
        parent = self.parent()
        return self._client._create_clone(parent=parent, part=self, **kwargs)

    def copy(
        self,
        target_parent: "Part",
        name: Optional[str] = None,
        include_children: bool = True,
        include_instances: bool = True,
    ) -> "Part":
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
        >>> model_to_copy = project.model(name='Model to be copied')
        >>> bike = project.model('Bike')
        >>> model_to_copy.copy(target_parent=bike, name='Copied model',
        >>>                    include_children=True,
        >>>                    include_instances=True)

        """
        check_type(target_parent, Part, "target_parent")

        if self.category != target_parent.category:
            # Cannot add a model under an instance or vice versa
            raise IllegalArgumentError(
                "part `{}` and target parent `{}`` must have the same category".format(
                    self, target_parent
                )
            )

        # to ensure that all properties are retrieved from the backend
        # as it might be the case that a part is retrieved in the context of a widget and there could be a possibility
        # that not all properties are retrieved we perform a refresh of the part itself first.
        self.refresh()

        from pykechain.extra_utils import _copy_part

        copied_part = _copy_part(
            part=self,
            target_parent=target_parent,
            name=name,
            include_children=include_children,
            include_instances=include_instances,
        )

        return copied_part

    def move(
        self,
        target_parent: "Part",
        name: Optional[str] = None,
        include_children: bool = True,
        include_instances: bool = True,
    ) -> "Part":
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
        >>> model_to_move = project.model(name='Model to be moved')
        >>> bike = project.model('Bike')
        >>> model_to_move.move(target_parent=bike, name='Moved model',
        >>>                    include_children=True,
        >>>                    include_instances=True)

        """
        copied_part = self.copy(
            target_parent=target_parent,
            name=name,
            include_children=include_children,
            include_instances=include_instances,
        )

        try:
            self.delete()
        except APIError:
            # In case of Part instances where the model has multiplicity 1 or 1-or-many, the model must be deleted
            model_of_instance = self.model()
            model_of_instance.delete()

        return copied_part

    def update(
        self,
        name: Optional[str] = None,
        update_dict: Optional[Dict] = None,
        properties_fvalues: Optional[List[Dict]] = None,
        **kwargs,
    ) -> None:
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
        :param kwargs: additional keyword-value arguments that will be passed into the part update request.
        :return: the updated :class:`Part`
        :raises NotFoundError: when the property name is not a valid property of this part
        :raises IllegalArgumentError: when the type or value of an argument provided is incorrect
        :raises APIError: in case an Error occurs

        Example
        -------
        >>> bike = project.part('Bike')
        >>> bike.update(name='Good name', update_dict={'Gears': 11, 'Total Height': 56.3})

        Example with properties_fvalues: <pyke Part 'Copied model under Bike' id 95d35be6>

        >>> bike = project.part('Bike')
        >>> bike.update(name='Good name',
        ...             properties_fvalues=[{'id': '95d35be6...', 'value': 11},
        ...                                 {'id': '7893cba4...', 'value': 56.3, 'value_options': {...}})

        """
        # dict(name=name, properties=json.dumps(update_dict))) with property ids:value
        # action = 'bulk_update_properties'  # not for KEC3
        check_text(name, "name")

        properties_fvalues, exception_fvalues, update_dict = self._parse_update_dict(
            self, properties_fvalues, update_dict
        )

        payload_json = dict(properties_fvalues=properties_fvalues, **kwargs)

        if name:
            payload_json.update(name=name)

        if Property._USE_BULK_UPDATE and not (name or kwargs):
            # Send updates to the property value in case of bulk updates while no part update is required
            for prop in self.properties:
                if prop.id in update_dict:
                    prop.value = update_dict[prop.id]
        else:
            response = self._client._request(
                "PUT",
                self._client._build_url("part", part_id=self.id),
                params=API_EXTRA_PARAMS["part"],
                json=payload_json,
            )

            if response.status_code != requests.codes.ok:  # pragma: no cover
                raise APIError(f"Could not update Part {self}", response=response)

            # update local properties (without a call)
            self.refresh(json=response.json()["results"][0])

        # If any values can not be set via the json, set them individually
        for exception_fvalue in exception_fvalues:
            self.property(exception_fvalue["id"]).value = exception_fvalue["value"]

    def delete(self) -> None:
        """Delete this part.

        :return: None
        :raises APIError: in case an Error occurs
        """
        response = self._client._request(
            "DELETE", self._client._build_url("part", part_id=self.id)
        )

        if response.status_code != requests.codes.no_content:  # pragma: no cover
            raise APIError(f"Could not delete Part {self}", response=response)

    def order_properties(
        self, property_list: Optional[List[Union["AnyProperty", str]]] = None
    ) -> None:
        """
        Order the properties of a part model using a list of property objects or property names or property id's.

        For KE-chain 3 backends, the order can also directly provided as a unique integer for each property in the
        `Part.update()` function if you provide the `properties_fvalues` list of dicts yourself. For more information
        please refer to the `Part.update()` documentation.

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
        if self.category != Category.MODEL:
            raise APIError(
                f"Ordering of properties must be done on a Part of category {Category.MODEL}."
            )

        property_ids = check_list_of_base(
            property_list, Property, "property_list", method=self.property
        )

        properties_fvalues = [
            dict(order=order, id=pk) for order, pk in enumerate(property_ids)
        ]

        return self.update(properties_fvalues=properties_fvalues)

    #
    # Utility Functions
    #

    def _repr_html_(self) -> str:
        """
        Represent the part in a HTML table for the use in notebooks.

        :return: html text
        :rtype: Text
        """
        html = [
            "<table width=100%>",
            f"<caption>{self.name}</caption>",
            "<tr>",
            "<th>Property</th>",
            "<th>Value</th>",
            "</tr>",
        ]

        for prop in self.properties:
            style = "color:blue;" if prop._json_data.get("output", False) else ""

            html.append(f'<tr style="{style}">')
            html.append(f"<td>{prop.name}</td>")
            html.append(f"<td>{prop.value}</td>")
            html.append("</tr>")

        html.append("</table>")

        return "".join(html)

    def as_dict(self) -> Dict:
        """
        Retrieve the properties of a part inside a dict in this structure: {property_name: property_value}.

        .. versionadded:: 1.9

        :returns: the values of the properties as a `dict`
        :rtype: dict

        Example
        -------
        >>> front_wheel = project.part('Front Wheel')
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

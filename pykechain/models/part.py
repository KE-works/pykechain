import requests

from pykechain.exceptions import NotFoundError, APIError
from pykechain.models import Base
from pykechain.utils import find


class Part(Base):
    """A virtual object representing a KE-chain part."""

    def __init__(self, json, **kwargs):
        """Construct a part from provided json data."""
        super(Part, self).__init__(json, **kwargs)

        self.category = json.get('category')
        self.parent_id = json['parent'].get('id') if 'parent' in json and json.get('parent') else None

        from pykechain.models import Property
        self.properties = [Property.create(p, client=self._client) for p in json['properties']]

    def property(self, name):
        """Retrieve the property with name belonging to this part.

        If you need to retrieve the property using eg. the id, use :meth:`pykechain.Client.properties`.

        :param name: property name to search for
        :return: a single :class:`pykechain.models.Property`
        :raises: NotFoundError

        Example
        -------

        >>> part = project.part('Bike')
        >>> gears = part.property('Gears')
        >>> gears.value
        6
        """
        found = find(self.properties, lambda p: name == p.name)

        if not found:
            raise NotFoundError("Could not find property with name {}".format(name))

        return found

    def parent(self):
        """The parent of this `Part`.

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
        """The children of this `Part` as `Partset`.

        :return: a set of `Part`s as :class:`pykechain.model.PartSet`. Will be empty if no children
        :raises: APIError

        Example
        -------

        >>> bike = project.part('Bike')
        >>> direct_descendants_of_bike = bike.children()
        """
        return self._client.parts(parent=self.id, category=self.category)

    def siblings(self):
        """The siblings of this `Part` as `Partset`.

        Siblings are other Parts sharing the same parent of this `Part`

        :return: a set of `Part`s as :class:`pykechain.model.PartSet`. Will be empty if no siblings
        :raises: APIError
        """
        if self.parent_id:
            return self._client.parts(parent=self.parent_id, category=self.category)
        else:
            from pykechain.models import PartSet
            return PartSet(parts=None)

    def add(self, model, **kwargs):
        """Add a new child to this part.

        :param model: model to use for the child
        :return: :class:`pykechain.models.Part`
        :raises: APIError
        """
        assert self.category == 'INSTANCE'

        return self._client.create_part(self, model, **kwargs)

    def add_to(self, parent, **kwargs):
        """Add a new instance of this model to a part.

        :param parent: part to add the new instance to
        :return: :class:`pykechain.models.Part`
        :raises: APIError
        """
        assert self.category == 'MODEL'

        return self._client.create_part(parent, self, **kwargs)

    def add_model(self, *args, **kwargs):
        """Add a new child model to this model.

        See :class:`pykechain.Client.create_model` for available parameters.

        :return: Part
        """
        assert self.category == 'MODEL'

        return self._client.create_model(self, *args, **kwargs)

    def add_property(self, *args, **kwargs):
        """Add a new property to this model.

        See :class:`pykechain.Client.create_property` for available parameters.

        :return: Property
        """
        assert self.category == 'MODEL'

        return self._client.create_property(self, *args, **kwargs)

    def delete(self):
        """Delete this part.

        :return: None
        :raises: APIError if delete was not succesfull
        """
        r = self._client._request('DELETE', self._client._build_url('part', part_id=self.id))

        if r.status_code != 204:
            raise APIError("Could not delete part: {} with id {}".format(self.name, self.id))

    def edit(self, name=None, description=None):
        """
        Edit the details of a part (model or instance).

        For an instance you can edit the Part instance name and the part instance description

        :param name: optional name of the part to edit
        :param description: optional description of the part
        :return: None
        :raises: APIError

        Example
        -------

        For changing a part
        >>> front_fork = project.part('Front Fork')
        >>> front_fork.edit(name='Front Fork - updated')
        >>> front_fork.edit(name='Front Fork cruizer', description='With my ragtop down so my hair can blow' )

        for changing a model
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

    def _repr_html_(self):
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

    def update(self, update_dict=None):
        # type: (dict) -> None
        """
        Use a dictionary with property names and property values to update the properties belonging to this part.

        :param update_dict: dictionary with keys being property names (str) and values being property values
        :return: :class:`pykechain.models.Part`
        :raises: APIError, Raises `NotFoundError` when the property name is not a valid property of this part

        Example
        -------

        >>> bike = client.scope('Bike Project').part('Bike')
        >>> bike.update({'Gears': 11, 'Total Height': 56.3})
        """
        assert type(update_dict) is dict, "update needs a dictionary with {'property_name': 'property_value', ... }"
        for property_name, property_value in update_dict.items():
            self.property(property_name).value = property_value

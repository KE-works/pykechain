from pykechain.exceptions import NotFoundError, APIError
from pykechain.models import Base
from pykechain.utils import find


class Part(Base):
    """A virtual object representing a KE-chain part."""

    def __init__(self, json, **kwargs):
        """Construct a part from provided json data."""
        super(Part, self).__init__(json, **kwargs)

        self.category = json.get('category')

        from pykechain.models import Property
        self.properties = [Property.create(p, client=self._client) for p in json['properties']]

    def property(self, name):
        """Retrieve property belonging to this part.

        :param name: property name to search for
        :return: a single :class:`pykechain.models.Property`
        :raises: NotFoundError
        """
        found = find(self.properties, lambda p: name == p.name)

        if not found:
            raise NotFoundError("Could not find property with name {}".format(name))

        return found

    def add(self, model, **kwargs):
        """Add a new child to this part.

        :param model: model to use for the child
        :return: :class:`pykechain.models.Part`
        :raises: APIError
        """
        return self._client.create_part(self, model, **kwargs)

    def add_to(self, parent, **kwargs):
        """Add a new instance of this model to a part.

        :param parent: part to add the new instance to
        :return: :class:`pykechain.models.Part`
        :raises: APIError
        """
        return self._client.create_part(parent, self, **kwargs)

    def delete(self):
        """Delete this part."""
        r = self._client._request('DELETE', self._client._build_url('part', part_id=self.id))

        if r.status_code != 204:
            raise APIError("Could not delete part: {} with id {}".format(self.name, self.id))

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

from pykechain.exceptions import NotFoundError, APIError
from pykechain.models import Base
from pykechain.utils import find


class Part(Base):

    def __init__(self, json, **kwargs):
        super(Part, self).__init__(json, **kwargs)

        self.category = json.get('category')

        from pykechain.models import Property
        self.properties = [Property.create(p, client=self._client) for p in json['properties']]

    def property(self, name):
        found = find(self.properties, lambda p: name == p.name)

        if not found:
            raise NotFoundError("Could not find property with name {}".format(name))

        return found

    def add(self, model, **kwargs):
        return self._post_instance(self, model, **kwargs)

    def add_to(self, parent, **kwargs):
        return self._post_instance(parent, self, **kwargs)

    def delete(self):
        r = self._client._request('DELETE', self._client._build_url('part', part_id=self.id))

        if r.status_code != 204:
            raise APIError("Could not delete part: {} with id {}".format(self.name, self.id))

    def _post_instance(self, parent, model, name=None):
        assert parent.category == 'INSTANCE'
        assert model.category == 'MODEL'

        if not name:
            name = model.name

        data = {
            "name": name,
            "parent": parent.id,
            "model": model.id
        }

        r = self._client._request('POST', self._client._build_url('parts'),
                                  params={"select_action": "new_instance"},
                                  data=data)

        if r.status_code != 201:
            raise APIError("Could not create part: {}".format(self.name))

        data = r.json()

        return Part(data['results'][0], client=self._client)

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

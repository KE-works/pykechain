from kechain2.models import Base
from kechain2.utils import find


class Part(Base):

    def __init__(self, json):
        super(Part, self).__init__(json)

        self.category = json.get('category')

        from kechain2.models import Property
        self.properties = [Property(p) for p in json['properties']]

    def property(self, name):
        found = find(self.properties, lambda p: name == p.name)

        assert found, "Could not find property with name {}".format(name)

        return found

    def add(self, model, **kwargs):
        return self._post_instance(self, model, **kwargs)

    def add_to(self, parent, **kwargs):
        return self._post_instance(parent, self, **kwargs)

    @classmethod
    def _post_instance(cls, parent, model, name=None):
        from kechain2.api import session, api_url, HEADERS

        assert parent.category == 'INSTANCE'
        assert model.category == 'MODEL'

        if not name:
            name = model.name

        r = session.post(api_url('parts'),
                         headers=HEADERS,
                         params={"select_action": "new_instance"},
                         data={
                             "name": name,
                             "parent": parent.id,
                             "model": model.id
                         })

        assert r.status_code == 201, "Could not create part"

        data = r.json()

        return Part(data['results'][0])

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

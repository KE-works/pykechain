import matplotlib.figure

from kechain2.utils import find


class Scope(object):

    def __init__(self, json):
        self._json_data = json

        self.id = json.get('id')
        self.name = json.get('name')
        self.bucket = json.get('bucket', {})

    def parts(self, *args, **kwargs):
        from .api import parts

        return parts(*args, bucket=self.bucket.get('id'), **kwargs)

    def part(self, *args, **kwargs):
        from .api import part

        return part(*args, bucket=self.bucket.get('id'), **kwargs)

    def model(self, *args, **kwargs):
        from .api import model

        return model(*args, bucket=self.bucket.get('id'), **kwargs)


class Activity(object):

    def __init__(self, json):
        self._json_data = json

        self.id = json.get('id')
        self.name = json.get('name')
        self.scope = json.get('scope')

    def parts(self, *args, **kwargs):
        from .api import parts

        return parts(*args, activity=self.id, **kwargs)


class Part(object):

    def __init__(self, json):
        self._json_data = json

        self.id = json.get('id')
        self.name = json.get('name')
        self.category = json.get('category')

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
                          params={
                              "select_action": "new_instance"
                          },
                          data={
                              "name": name,
                              "parent": parent.id,
                              "model": model.id
                          })

        assert r.status_code == 201, "Could not create part"

        data = r.json()

        return Part(data['results'][0])

    def _repr_html_(self):
        html = []

        html.append("<table width=100%>")
        html.append("<caption>{}</caption>".format(self.name))

        html.append("<tr>")
        html.append("<th>Property</th>")
        html.append("<th>Value</th>")
        html.append("</tr>")

        for prop in self.properties:
            html.append("<tr>")
            html.append("<td>{}</td>".format(prop.name))
            html.append("<td>{}</td>".format(prop.value))
            html.append("</tr>")

        html.append("</table>")

        return '' .join(html)


class Property(object):

    def __init__(self, json):
        self._json_data = json

        self.id = json.get('id')
        self.name = json.get('name')

        self._value = json.get('value')

    @property
    def value(self):
        return self._value

    @value.setter
    def value(self, value):
        if isinstance(value, matplotlib.figure.Figure):
            self._attach_plot(value)
            self._value = '<PLOT>'
            return

        if value != self._value:
            self._put_value(value)
            self._value = value

    @property
    def part(self):
        from .api import part

        part_id = self._json_data['part']

        return part(pk=part_id)

    def _put_value(self, value):
        from kechain2.api import session, api_url, HEADERS

        r = session.put(api_url('property', property_id=self.id),
                         headers=HEADERS,
                         json={'value': value})

        assert r.status_code == 200, "Could not update property value"

    def _post_attachment(self, data):
        from kechain2.api import session, api_url, HEADERS

        r = session.post(api_url('property_upload', property_id=self.id),
                          headers=HEADERS,
                          data={"part": self._json_data['part']},
                          files={"attachment": data})

        assert r.status_code == 200, "Could not upload attachment"

    def _attach_plot(self, figure):
        import io
        buffer = io.BytesIO()

        figure.savefig(buffer, format="png")

        data = ('plot.png', buffer.getvalue(), 'image/png')

        self._post_attachment(data)

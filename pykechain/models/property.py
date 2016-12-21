import io

from pykechain.models import Base


class Property(Base):

    def __init__(self, json, **kwargs):
        super(Property, self).__init__(json, **kwargs)

        self.output = json.get('output')

        self._value = json.get('value')

    @property
    def value(self):
        return self._value

    @value.setter
    def value(self, value):
        try:
            import matplotlib.figure

            if isinstance(value, matplotlib.figure.Figure):
                self._attach_plot(value)
                self._value = '<PLOT>'
                return
        except ImportError:
            pass

        if value != self._value:
            self._put_value(value)
            self._value = value

    @property
    def part(self):
        part_id = self._json_data['part']

        return self._client.part(pk=part_id)

    def _put_value(self, value):
        url = self._client._build_url('property', property_id=self.id)

        r = self._client._request('PUT', url, json={'value': value})

        assert r.status_code == 200, "Could not update property value"

    def _post_attachment(self, data):
        url = self._client._build_url('property_upload', property_id=self.id)

        r = self._client._request('POST', url,
                              data={"part": self._json_data['part']},
                              files={"attachment": data})

        assert r.status_code == 200, "Could not upload attachment"

    def _attach_plot(self, figure):
        buffer = io.BytesIO()

        figure.savefig(buffer, format="png")

        data = ('plot.png', buffer.getvalue(), 'image/png')

        self._post_attachment(data)
